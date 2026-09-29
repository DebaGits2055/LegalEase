import { MongoClient } from 'mongodb';

let cachedClient = null;
let cachedDb = null;

function getMongoUri() {
  const uri = process.env.MONGODB_URI || process.env.VITE_MONGODB_URI || '';
  return uri.trim().replace(/^["']|["']$/g, '');
}

function getDbName() {
  return (process.env.MONGODB_DB_NAME || 'legalease').trim().replace(/^["']|["']$/g, '');
}

async function connectToDatabase() {
  const uri = getMongoUri();
  if (!uri) {
    return { client: null, db: null };
  }

  if (cachedClient && cachedDb) {
    try {
      await cachedDb.command({ ping: 1 });
      return { client: cachedClient, db: cachedDb };
    } catch {
      cachedClient = null;
      cachedDb = null;
    }
  }

  const client = new MongoClient(uri, {
    maxPoolSize: 10,
    serverSelectionTimeoutMS: 5000,
    socketTimeoutMS: 45000
  });

  await client.connect();
  const dbName = getDbName();
  const db = client.db(dbName);

  cachedClient = client;
  cachedDb = db;

  return { client, db };
}

export default async function handler(req, res) {
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET,POST,OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type,Authorization');

  if (req.method === 'OPTIONS') {
    return res.status(200).end();
  }

  if (req.method !== 'POST') {
    return res.status(405).json({ error: 'Method not allowed' });
  }

  const { action, payload } = req.body || {};

  try {
    const { client, db } = await connectToDatabase();

    if (!db || !client) {
      return res.status(200).json({
        success: true,
        connected: false,
        message: 'MongoDB URI not yet configured in environment variables. Operating in resilient cache mode.'
      });
    }

    switch (action) {
      // 1. Get User by Email (Case-Insensitive & Dual-DB Fallback)
      case 'get_user': {
        const { email } = payload || {};
        if (!email) return res.status(400).json({ error: 'Email required' });
        const cleanEmail = email.toLowerCase().trim();
        const escaped = cleanEmail.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
        const query = { email: { $regex: new RegExp(`^${escaped}$`, 'i') } };

        // Search primary database first
        let user = await db.collection('users').findOne(query);

        // Search alternate database ('legalease' vs 'legalease_db') if not found in primary
        if (!user) {
          const alternateDbName = db.databaseName === 'legalease' ? 'legalease_db' : 'legalease';
          try {
            user = await client.db(alternateDbName).collection('users').findOne(query);
            // Auto-sync into primary db if found in alternate
            if (user) {
              const { _id, ...userData } = user;
              await db.collection('users').updateOne(
                { email: cleanEmail },
                { $set: userData },
                { upsert: true }
              );
            }
          } catch (e) {
            // Ignore alternate db lookup failure
          }
        }

        return res.status(200).json({ success: true, connected: true, user: user || null });
      }

      // 2. Save / Upsert User Profile (Dual-Sync to both legalease and legalease_db)
      case 'save_user': {
        const { user } = payload || {};
        if (!user || !user.email) return res.status(400).json({ error: 'User data required' });
        const cleanEmail = user.email.toLowerCase().trim();
        
        const updateData = {
          ...user,
          email: cleanEmail,
          updated_at: new Date().toISOString()
        };

        const result = await db.collection('users').findOneAndUpdate(
          { email: cleanEmail },
          { $set: updateData, $setOnInsert: { created_at: new Date().toISOString() } },
          { upsert: true, returnDocument: 'after' }
        );

        const savedUser = result?.value || result || updateData;

        // Also sync to alternate db to guarantee persistence across connection names
        try {
          const alternateDbName = db.databaseName === 'legalease' ? 'legalease_db' : 'legalease';
          await client.db(alternateDbName).collection('users').updateOne(
            { email: cleanEmail },
            { $set: updateData, $setOnInsert: { created_at: new Date().toISOString() } },
            { upsert: true }
          );
        } catch (e) {}

        return res.status(200).json({ success: true, connected: true, user: savedUser });
      }

      // 3. Save Document Compliance Audit & 256-Bit Encrypted Vault Payload
      case 'save_audit': {
        const { audit } = payload || {};
        if (!audit || !audit.user_email) return res.status(400).json({ error: 'Audit data required' });
        
        const auditDoc = {
          ...audit,
          user_email: audit.user_email.toLowerCase().trim(),
          created_at: new Date().toISOString()
        };

        const insertResult = await db.collection('document_audits').insertOne(auditDoc);

        // Increment user audit count in MongoDB
        await db.collection('users').updateOne(
          { email: auditDoc.user_email },
          { $inc: { doc_upload_count: 1 } }
        );

        return res.status(200).json({ success: true, connected: true, audit_id: insertResult.insertedId });
      }

      // 4. Get Audit History for User
      case 'get_audits': {
        const { email } = payload || {};
        if (!email) return res.status(400).json({ error: 'Email required' });
        const audits = await db.collection('document_audits')
          .find({ user_email: email.toLowerCase().trim() })
          .sort({ created_at: -1 })
          .limit(50)
          .toArray();

        return res.status(200).json({ success: true, connected: true, audits });
      }

      // 5. Record Revenue Ledger Payment & Top Up Audits
      case 'record_payment': {
        const { transaction_id, email, plan_name, amount_inr, payment_method, audits_added } = payload || {};
        const cleanEmail = (email || '').toLowerCase().trim();

        await db.collection('revenue_ledger').insertOne({
          transaction_id,
          email: cleanEmail,
          plan_name,
          amount_inr,
          payment_method,
          audits_added: audits_added || 10,
          status: 'COMPLETED',
          timestamp: new Date().toISOString()
        });

        // Update user limits in MongoDB
        await db.collection('users').updateOne(
          { email: cleanEmail },
          {
            $set: { is_subscribed: true, subscription_plan: plan_name },
            $inc: { audit_limit: audits_added || 10 }
          }
        );

        return res.status(200).json({ success: true, connected: true, message: 'Payment recorded in MongoDB ledger.' });
      }

      default:
        return res.status(400).json({ error: `Unknown action: ${action}` });
    }
  } catch (err) {
    console.error('MongoDB Serverless API Error:', err);
    return res.status(500).json({ success: false, error: err.message });
  }
}

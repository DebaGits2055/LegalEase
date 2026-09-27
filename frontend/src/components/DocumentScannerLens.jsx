import React, { useState, useRef, useEffect } from 'react';
import { Crop, RotateCw, Check, X, Sparkles, Sliders, Maximize2, ShieldCheck } from 'lucide-react';

export default function DocumentScannerLens({ 
  imageSrc, 
  onCropComplete, 
  onCancel 
}) {
  const [rotation, setRotation] = useState(0); // 0, 90, 180, 270
  const [filterMode, setFilterMode] = useState('enhanced'); // 'original', 'enhanced', 'bw'
  
  // Crop percentages (0 to 100)
  const [crop, setCrop] = useState({
    x: 8,
    y: 8,
    width: 84,
    height: 84
  });

  const [activeHandle, setActiveHandle] = useState(null); // 'tl', 'tr', 'bl', 'br', 'move'
  const containerRef = useRef(null);
  const imageRef = useRef(null);

  // Rotate image clockwise by 90 degrees
  const handleRotate = () => {
    setRotation(prev => (prev + 90) % 360);
  };

  // Touch and Mouse handlers for dragging Google Lens corners
  const handleDragStart = (handle, e) => {
    e.preventDefault();
    e.stopPropagation();
    setActiveHandle(handle);
  };

  useEffect(() => {
    const handleMove = (clientX, clientY) => {
      if (!activeHandle || !containerRef.current) return;
      const rect = containerRef.current.getBoundingClientRect();
      
      const px = Math.max(0, Math.min(100, ((clientX - rect.left) / rect.width) * 100));
      const py = Math.max(0, Math.min(100, ((clientY - rect.top) / rect.height) * 100));

      setCrop(prev => {
        let { x, y, width, height } = prev;
        const minSize = 15;

        if (activeHandle === 'tl') {
          const newWidth = x + width - px;
          const newHeight = y + height - py;
          if (newWidth >= minSize && newHeight >= minSize) {
            return { x: px, y: py, width: newWidth, height: newHeight };
          }
        } else if (activeHandle === 'tr') {
          const newWidth = px - x;
          const newHeight = y + height - py;
          if (newWidth >= minSize && newHeight >= minSize) {
            return { x, y: py, width: newWidth, height: newHeight };
          }
        } else if (activeHandle === 'bl') {
          const newWidth = x + width - px;
          const newHeight = py - y;
          if (newWidth >= minSize && newHeight >= minSize) {
            return { x: px, y, width: newWidth, height: newHeight };
          }
        } else if (activeHandle === 'br') {
          const newWidth = px - x;
          const newHeight = py - y;
          if (newWidth >= minSize && newHeight >= minSize) {
            return { x, y, width: newWidth, height: newHeight };
          }
        }
        return prev;
      });
    };

    const onMouseMove = (e) => handleMove(e.clientX, e.clientY);
    const onTouchMove = (e) => {
      if (e.touches && e.touches.length > 0) {
        handleMove(e.touches[0].clientX, e.touches[0].clientY);
      }
    };

    const onEnd = () => setActiveHandle(null);

    if (activeHandle) {
      window.addEventListener('mousemove', onMouseMove);
      window.addEventListener('mouseup', onEnd);
      window.addEventListener('touchmove', onTouchMove);
      window.addEventListener('touchend', onEnd);
    }

    return () => {
      window.removeEventListener('mousemove', onMouseMove);
      window.removeEventListener('mouseup', onEnd);
      window.removeEventListener('touchmove', onTouchMove);
      window.removeEventListener('touchend', onEnd);
    };
  }, [activeHandle]);

  // Crop & Enhance execution via hidden canvas
  const handleApplyCrop = () => {
    const img = imageRef.current;
    if (!img) return;

    const naturalWidth = img.naturalWidth || 1200;
    const naturalHeight = img.naturalHeight || 1600;

    const canvas = document.createElement('canvas');
    const ctx = canvas.getContext('2d');

    // Calculate source rect
    const srcX = (crop.x / 100) * naturalWidth;
    const srcY = (crop.y / 100) * naturalHeight;
    const srcW = (crop.width / 100) * naturalWidth;
    const srcH = (crop.height / 100) * naturalHeight;

    // Handle rotation dimensions
    if (rotation === 90 || rotation === 270) {
      canvas.width = srcH;
      canvas.height = srcW;
    } else {
      canvas.width = srcW;
      canvas.height = srcH;
    }

    ctx.save();
    if (rotation === 90) {
      ctx.translate(canvas.width, 0);
      ctx.rotate((90 * Math.PI) / 180);
      ctx.drawImage(img, srcX, srcY, srcW, srcH, 0, 0, srcW, srcH);
    } else if (rotation === 180) {
      ctx.translate(canvas.width, canvas.height);
      ctx.rotate((180 * Math.PI) / 180);
      ctx.drawImage(img, srcX, srcY, srcW, srcH, 0, 0, srcW, srcH);
    } else if (rotation === 270) {
      ctx.translate(0, canvas.height);
      ctx.rotate((270 * Math.PI) / 180);
      ctx.drawImage(img, srcX, srcY, srcW, srcH, 0, 0, srcW, srcH);
    } else {
      ctx.drawImage(img, srcX, srcY, srcW, srcH, 0, 0, srcW, srcH);
    }
    ctx.restore();

    // Apply Document Filter
    if (filterMode === 'enhanced' || filterMode === 'bw') {
      const imgData = ctx.getImageData(0, 0, canvas.width, canvas.height);
      const d = imgData.data;
      for (let i = 0; i < d.length; i += 4) {
        const r = d[i];
        const g = d[i + 1];
        const b = d[i + 2];
        const gray = 0.299 * r + 0.587 * g + 0.114 * b;

        if (filterMode === 'bw') {
          // Sharp binary document contrast
          const threshold = gray > 140 ? 255 : Math.max(0, gray * 0.7);
          d[i] = threshold;
          d[i + 1] = threshold;
          d[i + 2] = threshold;
        } else {
          // Auto-contrast enhancement for faint text & legal stamps
          const enhanced = Math.min(255, Math.max(0, (gray - 128) * 1.35 + 128));
          d[i] = enhanced;
          d[i + 1] = enhanced;
          d[i + 2] = enhanced;
        }
      }
      ctx.putImageData(imgData, 0, 0);
    }

    canvas.toBlob((blob) => {
      if (blob) {
        const croppedFile = new File([blob], 'lens_scanned_document.png', { type: 'image/png' });
        onCropComplete(croppedFile, canvas.toDataURL('image/png'));
      }
    }, 'image/png', 0.95);
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-3 sm:p-6 bg-slate-950/80 backdrop-blur-md animate-in fade-in duration-200">
      <div className="bg-white rounded-3xl max-w-2xl w-full p-4 sm:p-6 shadow-2xl border border-slate-200 flex flex-col max-h-[92vh] overflow-hidden">
        
        {/* Header Bar */}
        <div className="flex items-center justify-between pb-3 border-b border-slate-100 mb-3">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 rounded-xl bg-blue-600 text-white flex items-center justify-center shadow-xs">
              <Crop className="w-4 h-4" />
            </div>
            <div>
              <h4 className="text-sm sm:text-base font-extrabold text-slate-900 leading-tight">
                Google Lens Document Scanner
              </h4>
              <p className="text-[11px] text-slate-500 font-medium">
                Adjust the 4 corners to crop document boundaries and filter noise.
              </p>
            </div>
          </div>
          <button
            onClick={onCancel}
            className="p-1.5 rounded-full hover:bg-slate-100 text-slate-400 hover:text-slate-700 transition-all cursor-pointer"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Interactive Cropper Viewport */}
        <div 
          ref={containerRef}
          className="relative flex-1 bg-slate-950 rounded-2xl overflow-hidden flex items-center justify-center select-none min-h-[300px] max-h-[480px]"
          style={{ touchAction: 'none' }}
        >
          <img
            ref={imageRef}
            src={imageSrc}
            alt="Captured Legal Document"
            className="max-h-full max-w-full object-contain pointer-events-none transition-transform duration-200"
            style={{
              transform: `rotate(${rotation}deg)`,
              filter: filterMode === 'bw' ? 'grayscale(100%) contrast(150%)' : filterMode === 'enhanced' ? 'contrast(125%) brightness(105%)' : 'none'
            }}
          />

          {/* Dark Overlay outside crop area */}
          <div 
            className="absolute border-2 border-blue-400 shadow-[0_0_0_9999px_rgba(15,23,42,0.65)] pointer-events-none"
            style={{
              left: `${crop.x}%`,
              top: `${crop.y}%`,
              width: `${crop.width}%`,
              height: `${crop.height}%`,
            }}
          >
            {/* Rule-of-Thirds Document Grid Lines */}
            <div className="absolute inset-0 grid grid-cols-3 grid-rows-3 pointer-events-none opacity-40">
              <div className="border-r border-b border-blue-200" />
              <div className="border-r border-b border-blue-200" />
              <div className="border-b border-blue-200" />
              <div className="border-r border-b border-blue-200" />
              <div className="border-r border-b border-blue-200" />
              <div className="border-b border-blue-200" />
              <div className="border-r border-blue-200" />
              <div className="border-r border-blue-200" />
              <div />
            </div>

            <div className="absolute top-2 left-2 bg-blue-600/90 text-white text-[9px] font-extrabold px-1.5 py-0.5 rounded shadow-xs uppercase tracking-wide">
              Document Area
            </div>
          </div>

          {/* 4 Draggable Corner Handles (Google Lens Style) */}
          {/* Top-Left */}
          <div
            onMouseDown={(e) => handleDragStart('tl', e)}
            onTouchStart={(e) => handleDragStart('tl', e)}
            className="absolute w-7 h-7 -translate-x-1/2 -translate-y-1/2 bg-white border-2 border-blue-600 rounded-full shadow-lg cursor-nwse-resize z-20 flex items-center justify-center"
            style={{ left: `${crop.x}%`, top: `${crop.y}%` }}
          >
            <div className="w-2 h-2 rounded-full bg-blue-600" />
          </div>

          {/* Top-Right */}
          <div
            onMouseDown={(e) => handleDragStart('tr', e)}
            onTouchStart={(e) => handleDragStart('tr', e)}
            className="absolute w-7 h-7 -translate-x-1/2 -translate-y-1/2 bg-white border-2 border-blue-600 rounded-full shadow-lg cursor-nesw-resize z-20 flex items-center justify-center"
            style={{ left: `${crop.x + crop.width}%`, top: `${crop.y}%` }}
          >
            <div className="w-2 h-2 rounded-full bg-blue-600" />
          </div>

          {/* Bottom-Left */}
          <div
            onMouseDown={(e) => handleDragStart('bl', e)}
            onTouchStart={(e) => handleDragStart('bl', e)}
            className="absolute w-7 h-7 -translate-x-1/2 -translate-y-1/2 bg-white border-2 border-blue-600 rounded-full shadow-lg cursor-nesw-resize z-20 flex items-center justify-center"
            style={{ left: `${crop.x}%`, top: `${crop.y + crop.height}%` }}
          >
            <div className="w-2 h-2 rounded-full bg-blue-600" />
          </div>

          {/* Bottom-Right */}
          <div
            onMouseDown={(e) => handleDragStart('br', e)}
            onTouchStart={(e) => handleDragStart('br', e)}
            className="absolute w-7 h-7 -translate-x-1/2 -translate-y-1/2 bg-white border-2 border-blue-600 rounded-full shadow-lg cursor-nwse-resize z-20 flex items-center justify-center"
            style={{ left: `${crop.x + crop.width}%`, top: `${crop.y + crop.height}%` }}
          >
            <div className="w-2 h-2 rounded-full bg-blue-600" />
          </div>

        </div>

        {/* Toolbar Controls */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pt-3 mt-2 border-t border-slate-100">
          
          {/* Filters & Rotate */}
          <div className="flex items-center gap-2 flex-wrap">
            <button
              type="button"
              onClick={handleRotate}
              className="py-1.5 px-3 bg-slate-100 hover:bg-slate-200 text-slate-700 font-bold text-xs rounded-xl flex items-center gap-1.5 transition-all cursor-pointer"
            >
              <RotateCw className="w-3.5 h-3.5" />
              <span>Rotate 90°</span>
            </button>

            {/* Filter pills */}
            <div className="flex items-center p-1 bg-slate-100 rounded-xl">
              <button
                type="button"
                onClick={() => setFilterMode('original')}
                className={`py-1 px-2.5 rounded-lg text-[11px] font-bold transition-all cursor-pointer ${filterMode === 'original' ? 'bg-white text-blue-700 shadow-xs' : 'text-slate-600'}`}
              >
                Original
              </button>
              <button
                type="button"
                onClick={() => setFilterMode('enhanced')}
                className={`py-1 px-2.5 rounded-lg text-[11px] font-bold transition-all cursor-pointer ${filterMode === 'enhanced' ? 'bg-white text-blue-700 shadow-xs' : 'text-slate-600'}`}
              >
                Auto-Enhanced
              </button>
              <button
                type="button"
                onClick={() => setFilterMode('bw')}
                className={`py-1 px-2.5 rounded-lg text-[11px] font-bold transition-all cursor-pointer ${filterMode === 'bw' ? 'bg-white text-blue-700 shadow-xs' : 'text-slate-600'}`}
              >
                B&W Doc
              </button>
            </div>
          </div>

          {/* Action Buttons */}
          <div className="flex items-center gap-2">
            <button
              type="button"
              onClick={onCancel}
              className="flex-1 sm:flex-none py-2 px-4 bg-slate-100 hover:bg-slate-200 text-slate-700 font-bold text-xs rounded-xl transition-all cursor-pointer"
            >
              Cancel
            </button>
            <button
              type="button"
              onClick={handleApplyCrop}
              className="flex-1 sm:flex-none py-2 px-5 bg-blue-600 hover:bg-blue-700 text-white font-bold text-xs rounded-xl shadow-md transition-all flex items-center justify-center gap-1.5 cursor-pointer"
            >
              <Check className="w-4 h-4" />
              <span>Confirm & Audit Document</span>
            </button>
          </div>

        </div>

      </div>
    </div>
  );
}

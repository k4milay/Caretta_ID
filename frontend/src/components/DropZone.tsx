import { useRef, useState, DragEvent, ChangeEvent } from "react";
import "./DropZone.css";

interface Props {
  onFile: (file: File) => void;
  accept?: string;
}

export default function DropZone({ onFile, accept = "image/*" }: Props) {
  const inputRef = useRef<HTMLInputElement>(null);
  const [dragging, setDragging] = useState(false);
  const [preview, setPreview] = useState<string | null>(null);

  function handle(file: File) {
    setPreview(URL.createObjectURL(file));
    onFile(file);
  }

  function onChange(e: ChangeEvent<HTMLInputElement>) {
    const f = e.target.files?.[0];
    if (f) handle(f);
  }

  function onDrop(e: DragEvent) {
    e.preventDefault();
    setDragging(false);
    const f = e.dataTransfer.files[0];
    if (f) handle(f);
  }

  return (
    <div
      className={`dropzone ${dragging ? "dragging" : ""} ${preview ? "has-preview" : ""}`}
      onClick={() => inputRef.current?.click()}
      onDragOver={(e) => { e.preventDefault(); setDragging(true); }}
      onDragLeave={() => setDragging(false)}
      onDrop={onDrop}
    >
      <input ref={inputRef} type="file" accept={accept} onChange={onChange} hidden />
      {preview ? (
        <img src={preview} alt="önizleme" className="dropzone-preview" />
      ) : (
        <>
          <div className="dropzone-icon">📷</div>
          <div className="dropzone-label">
            Fotoğraf yüklemek için tıklayın<br />
            <span style={{ color: "var(--muted)", fontWeight: 400 }}>veya sürükleyip bırakın</span>
          </div>
          <div className="dropzone-sub">JPG, PNG, WEBP</div>
        </>
      )}
    </div>
  );
}

import { useRef, useState, DragEvent, ChangeEvent } from "react";
import "./DropZone.css";

interface Props {
  onFile: (file: File) => void;
  accept?: string;
  label?: string;
}

export default function DropZone({ onFile, accept = "image/*", label = "Fotoğraf yüklemek için tıklayın veya sürükleyin" }: Props) {
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
      {preview
        ? <img src={preview} alt="önizleme" className="dropzone-preview" />
        : <span className="dropzone-label">📷 {label}</span>
      }
    </div>
  );
}

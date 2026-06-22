// components/DocumentThumbnail.jsx

export default function DocumentThumbnail({
  title,
  digitized,
  failedTasks,
  className,
}) {
  return (
    <div className={`flex flex-col rounded-lg p-2 ${className}`}>
        <h4>
            {title}
        </h4>

        <div className="flex flex-col">
            <span className="font-bold">Digitized:</span>
            <span>{String(digitized)}</span>
        </div>

        <div className="flex flex-col">
            <span className="font-bold">Num. Failed Tasks:</span>
            <span>{failedTasks}</span>
        </div>
    </div>
  )
}

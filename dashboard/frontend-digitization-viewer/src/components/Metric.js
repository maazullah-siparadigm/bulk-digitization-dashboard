// components/Metric.jsx

export default function Metric({
  title,
  value,
  subtitle,
  className = "",
}) {
  return (
    <div className={`rounded-lg p-6 ${className}`}>
      <h3 className="font-semibold text-black">
        {title}
      </h3>

      {value != null && (
        <p className="text-gray-400 mt-2">
          {value}
        </p>
      )}

      {subtitle != null && (
        <p className="text-gray-500 text-xs mt-1">
          {subtitle}
        </p>
      )}
    </div>
  )
}
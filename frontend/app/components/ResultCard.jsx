export default function ResultCard({ data }) {
  return (
    <div className="mt-6 p-4 border rounded-xl bg-gray-50 shadow">
      <h2 className="text-lg font-semibold">Result</h2>
      <p className="mt-2 text-gray-700">Status: {data.status}</p>
      {data.confidence && <p>Confidence: {(data.confidence * 100).toFixed(2)}%</p>}
      {data.message && <p>{data.message}</p>}
    </div>
  );
}

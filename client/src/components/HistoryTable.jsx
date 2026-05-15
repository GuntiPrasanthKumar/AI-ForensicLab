import { FileText, Upload, Trash2 } from "lucide-react";
import { motion } from "framer-motion";

const HistoryTable = ({ history, deleteHistoryItem }) => {
  return (
    <motion.div 
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="glass-card rounded-3xl overflow-hidden"
    >
      <div className="p-6 border-b border-white/5 flex justify-between items-center">
        <h2 className="text-xl font-bold text-white">Analysis History</h2>
        <span className="text-sm text-gray-500">{history.length} records found</span>
      </div>
      <div className="overflow-x-auto">
        <table className="w-full text-left text-gray-300">
          <thead className="bg-white/5 text-gray-400 text-xs uppercase">
            <tr>
              <th className="px-6 py-4">Content</th>
              <th className="px-6 py-4">AI Prob.</th>
              <th className="px-6 py-4">Confidence</th>
              <th className="px-6 py-4">Date</th>
              <th className="px-6 py-4">Action</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-white/5">
            {history.map((item) => (
              <tr key={item._id} className="hover:bg-white/5 transition-all group">
                <td className="px-6 py-4">
                  <div className="flex items-center gap-3">
                    <div className={`p-2 rounded-lg ${item.inputType === 'text' ? 'bg-purple-500/10 text-purple-400' : 'bg-blue-500/10 text-blue-400'}`}>
                      {item.inputType === 'text' ? <FileText size={16} /> : <Upload size={16} />}
                    </div>
                    <span className="font-medium truncate max-w-[150px]">{item.filename}</span>
                  </div>
                </td>
                <td className="px-6 py-4">
                  <span className={`font-bold ${item.aiProbability > 70 ? 'text-red-400' : 'text-green-400'}`}>
                    {item.aiProbability}%
                  </span>
                </td>
                <td className="px-6 py-4">
                  <span className="px-2 py-1 bg-white/10 rounded text-[10px] uppercase font-bold tracking-wider">
                    {item.confidence}
                  </span>
                </td>
                <td className="px-6 py-4 text-gray-500 text-sm">
                  {new Date(item.createdAt).toLocaleDateString()}
                </td>
                <td className="px-6 py-4">
                  <button 
                    onClick={() => deleteHistoryItem(item._id)}
                    className="p-2 text-gray-500 hover:text-red-400 transition-all opacity-0 group-hover:opacity-100"
                  >
                    <Trash2 size={18} />
                  </button>
                </td>
              </tr>
            ))}
            {history.length === 0 && (
              <tr>
                <td colSpan="5" className="px-6 py-12 text-center text-gray-500">No history records yet.</td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </motion.div>
  );
};

export default HistoryTable;

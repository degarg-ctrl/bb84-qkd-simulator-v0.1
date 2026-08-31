import { useState, useEffect } from 'react';
import useSimulationStore from '../../store/simulationStore';

export default function LoadExperimentModal({ isOpen, onClose }) {
  const [experiments, setExperiments] = useState([]);
  const setParams = useSimulationStore((state) => state.setParams);
  const setSourceModel = useSimulationStore((state) => state.setSourceModel);

  useEffect(() => {
    if (isOpen) {
      const saved = JSON.parse(localStorage.getItem('qkd-experiments') || '[]');
      setExperiments(saved);
    }
  }, [isOpen]);

  if (!isOpen) return null;

  const handleLoad = (experiment) => {
    setParams(experiment.params);
    setSourceModel(experiment.sourceModel || 'ideal');
    onClose();
  };

  const handleDelete = (id) => {
    const updated = experiments.filter(exp => exp.id !== id);
    localStorage.setItem('qkd-experiments', JSON.stringify(updated));
    setExperiments(updated);
  };

  const handleExport = (experiment) => {
    const dataStr = JSON.stringify(experiment, null, 2);
    const dataBlob = new Blob([dataStr], { type: 'application/json' });
    const url = URL.createObjectURL(dataBlob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `${experiment.name.replace(/\s+/g, '_')}.json`;
    link.click();
  };

  const handleImport = () => {
    const input = document.createElement('input');
    input.type = 'file';
    input.accept = '.json';
    input.onchange = (e) => {
      const file = e.target.files[0];
      const reader = new FileReader();
      reader.onload = (event) => {
        try {
          const experiment = JSON.parse(event.target.result);
          const saved = JSON.parse(localStorage.getItem('qkd-experiments') || '[]');
          saved.push({ ...experiment, id: Date.now().toString() });
          localStorage.setItem('qkd-experiments', JSON.stringify(saved));
          setExperiments(saved);
        } catch (err) {
          alert('Invalid experiment file');
        }
      };
      reader.readAsText(file);
    };
    input.click();
  };

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <div className="border rounded-lg p-6 w-[600px] max-h-[80vh] overflow-y-auto shadow-2xl"
           style={{ backgroundColor: 'var(--panel-bg)', borderColor: 'var(--border-color)' }}>
        <div className="flex justify-between items-center mb-4">
          <h2 className="text-xl font-semibold text-cyan-400 font-mono">Load Experiment</h2>
          <button
            onClick={handleImport}
            className="text-xs border px-3 py-1.5 rounded font-mono transition-colors"
            style={{
              backgroundColor: 'var(--card-bg)',
              borderColor: 'var(--card-border)',
              color: 'var(--text-primary)'
            }}
          >
            Import JSON
          </button>
        </div>

        {experiments.length === 0 ? (
          <p className="text-center py-8 font-mono text-sm" style={{ color: 'var(--text-muted)' }}>No saved experiments</p>
        ) : (
          <div className="space-y-2">
            {experiments.map((exp) => (
              <div key={exp.id} className="border rounded p-3"
                   style={{ backgroundColor: 'var(--card-bg)', borderColor: 'var(--card-border)' }}>
                <div className="flex justify-between items-start mb-2">
                  <div>
                    <h3 className="font-semibold font-mono text-sm" style={{ color: 'var(--text-primary)' }}>{exp.name}</h3>
                    {exp.description && (
                      <p className="text-xs mt-0.5" style={{ color: 'var(--text-muted)' }}>{exp.description}</p>
                    )}
                    <p className="text-xs mt-1 font-mono" style={{ color: 'var(--text-subtle)' }}>
                      {new Date(exp.createdAt).toLocaleDateString()}
                    </p>
                  </div>
                  <div className="flex gap-1">
                    <button
                      onClick={() => handleLoad(exp)}
                      className="text-xs bg-cyan-600 hover:bg-cyan-700 text-white font-mono px-2 py-1 rounded"
                    >
                      Load
                    </button>
                    <button
                      onClick={() => handleExport(exp)}
                      className="text-xs border font-mono px-2 py-1 rounded transition-colors"
                      style={{
                        backgroundColor: 'var(--panel-bg)',
                        borderColor: 'var(--border-color)',
                        color: 'var(--text-muted)'
                      }}
                    >
                      Export
                    </button>
                    <button
                      onClick={() => handleDelete(exp.id)}
                      className="text-xs bg-red-600 hover:bg-red-700 text-white font-mono px-2 py-1 rounded"
                    >
                      Delete
                    </button>
                  </div>
                </div>
                <div className="text-xs font-mono" style={{ color: 'var(--text-subtle)' }}>
                  {exp.params.n_bits} bits, {exp.params.distance_km}km, {exp.sourceModel}
                </div>
              </div>
            ))}
          </div>
        )}

        <button
          onClick={onClose}
          className="w-full mt-4 border font-mono text-sm px-4 py-2 rounded transition-colors"
          style={{
            backgroundColor: 'var(--card-bg)',
            borderColor: 'var(--card-border)',
            color: 'var(--text-muted)'
          }}
        >
          Close
        </button>
      </div>
    </div>
  );
}

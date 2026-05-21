import React, { useState } from 'react';
import { X, Plus, Trash2 } from 'lucide-react';
import { createPlaybookAPI } from '../../api/client';

interface PlaybookBuilderModalProps {
    onClose: () => void;
    onSuccess: () => void;
}

export function PlaybookBuilderModal({ onClose, onSuccess }: PlaybookBuilderModalProps) {
    const [name, setName] = useState('');
    const [description, setDescription] = useState('');
    const [triggerSeverities, setTriggerSeverities] = useState<string[]>(['High']);

    // Rule builder state
    const [rules, setRules] = useState([{ field: 'raw_data.event_type', op: '==', value: '' }]);

    // Actions builder state
    const [actions, setActions] = useState([{ name: 'notify_slack', params: '{}' }]);

    const [error, setError] = useState<string | null>(null);
    const [isSubmitting, setIsSubmitting] = useState(false);

    const availableSeverities = ['Critical', 'High', 'Medium', 'Low', 'Info'];
    const availableActions = ['notify_slack', 'block_ip', 'isolate_host', 'create_jira_ticket'];

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setError(null);
        setIsSubmitting(true);

        try {
            // Parse the action params JSON strings back into objects
            const parsedActions = actions.map(a => ({
                id: a.name,
                name: a.name,
                params: JSON.parse(a.params)
            }));

            const payload = {
                name,
                description,
                is_active: true,
                trigger_severity: triggerSeverities,
                steps_definition: {
                    conditions: [
                        {
                            operator: "AND",
                            rules: rules
                        }
                    ],
                    actions: parsedActions
                }
            };

            await createPlaybookAPI(payload);
            onSuccess();
        } catch (err: any) {
            setError(err.message || 'Failed to parse JSON parameters or create playbook');
        } finally {
            setIsSubmitting(false);
        }
    };

    const handleSeverityToggle = (sev: string) => {
        setTriggerSeverities(prev =>
            prev.includes(sev) ? prev.filter(s => s !== sev) : [...prev, sev]
        );
    };

    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 overflow-y-auto">
            <div className="bg-slate-900 border border-slate-700 rounded-xl max-w-2xl w-full m-4 max-h-[90vh] flex flex-col shadow-2xl">
                <div className="p-6 border-b border-slate-800 flex justify-between items-center sticky top-0 bg-slate-900 rounded-t-xl z-10">
                    <h2 className="text-xl font-bold text-white">Create Automation Playbook</h2>
                    <button onClick={onClose} className="p-2 text-slate-400 hover:text-white rounded-lg hover:bg-slate-800 transition-colors">
                        <X className="w-5 h-5" />
                    </button>
                </div>

                <div className="p-6 overflow-y-auto custom-scrollbar">
                    <form id="playbook-form" onSubmit={handleSubmit} className="space-y-8">
                        {error && (
                            <div className="p-4 bg-red-500/10 border border-red-500/50 rounded-lg text-red-400 text-sm">
                                {error}
                            </div>
                        )}

                        {/* Basic Info */}
                        <div className="space-y-4">
                            <h3 className="text-lg font-medium text-white border-b border-slate-800 pb-2">1. Playbook Details</h3>
                            <div>
                                <label className="block text-sm font-medium text-slate-300 mb-1">Playbook Name</label>
                                <input
                                    type="text" required value={name} onChange={e => setName(e.target.value)}
                                    className="w-full bg-slate-800 border border-slate-700 rounded-lg px-4 py-2 text-white focus:outline-none focus:border-blue-500"
                                    placeholder="e.g., Block Malicious IPs"
                                />
                            </div>
                            <div>
                                <label className="block text-sm font-medium text-slate-300 mb-1">Description</label>
                                <textarea
                                    value={description} onChange={e => setDescription(e.target.value)}
                                    className="w-full bg-slate-800 border border-slate-700 rounded-lg px-4 py-2 text-white focus:outline-none focus:border-blue-500"
                                    placeholder="What does this playbook do?" rows={2}
                                />
                            </div>
                            <div>
                                <label className="block text-sm font-medium text-slate-300 mb-2">Trigger Severities</label>
                                <div className="flex flex-wrap gap-2">
                                    {availableSeverities.map(sev => (
                                        <button
                                            key={sev} type="button" onClick={() => handleSeverityToggle(sev)}
                                            className={`px-3 py-1.5 rounded-lg text-sm font-medium border transition-colors ${triggerSeverities.includes(sev)
                                                    ? 'bg-blue-500/20 border-blue-500 text-blue-400'
                                                    : 'bg-slate-800 border-slate-700 text-slate-400 hover:border-slate-500'
                                                }`}
                                        >
                                            {sev}
                                        </button>
                                    ))}
                                </div>
                            </div>
                        </div>

                        {/* Evaluation Conditions */}
                        <div className="space-y-4">
                            <h3 className="text-lg font-medium text-white border-b border-slate-800 pb-2 flex justify-between items-center">
                                <span>2. Evaluation Conditions</span>
                                <button
                                    type="button"
                                    onClick={() => setRules([...rules, { field: '', op: '==', value: '' }])}
                                    className="text-xs flex items-center gap-1 text-blue-400 hover:text-blue-300"
                                >
                                    <Plus className="w-3 h-3" /> Add Rule
                                </button>
                            </h3>

                            <div className="space-y-3">
                                {rules.map((rule, idx) => (
                                    <div key={idx} className="flex gap-2 items-center bg-slate-800/50 p-3 rounded-lg border border-slate-700/50">
                                        <input
                                            type="text" placeholder="Field (e.g. risk_score)" value={rule.field}
                                            onChange={e => { const newRules = [...rules]; newRules[idx].field = e.target.value; setRules(newRules); }}
                                            className="flex-1 bg-slate-800 border border-slate-700 rounded text-sm px-3 py-1.5 text-white focus:border-blue-500 outline-none"
                                        />
                                        <select
                                            value={rule.op}
                                            onChange={e => { const newRules = [...rules]; newRules[idx].op = e.target.value; setRules(newRules); }}
                                            className="bg-slate-800 border border-slate-700 rounded text-sm px-3 py-1.5 text-white focus:border-blue-500 outline-none w-24"
                                        >
                                            <option value="==">==</option>
                                            <option value="!=">!=</option>
                                            <option value=">">&gt;</option>
                                            <option value="<">&lt;</option>
                                            <option value="in">in list</option>
                                        </select>
                                        <input
                                            type="text" placeholder="Value" value={rule.value}
                                            onChange={e => { const newRules = [...rules]; newRules[idx].value = e.target.value; setRules(newRules); }}
                                            className="flex-1 bg-slate-800 border border-slate-700 rounded text-sm px-3 py-1.5 text-white focus:border-blue-500 outline-none"
                                        />
                                        <button
                                            type="button"
                                            onClick={() => setRules(rules.filter((_, i) => i !== idx))}
                                            className="p-1 px-2 text-slate-500 hover:text-red-400"
                                            disabled={rules.length === 1}
                                        >
                                            <Trash2 className="w-4 h-4" />
                                        </button>
                                    </div>
                                ))}
                            </div>
                        </div>

                        {/* Execution Actions */}
                        <div className="space-y-4">
                            <h3 className="text-lg font-medium text-white border-b border-slate-800 pb-2 flex justify-between items-center">
                                <span>3. Execution Actions</span>
                                <button
                                    type="button"
                                    onClick={() => setActions([...actions, { name: 'notify_slack', params: '{}' }])}
                                    className="text-xs flex items-center gap-1 text-blue-400 hover:text-blue-300"
                                >
                                    <Plus className="w-3 h-3" /> Add Action
                                </button>
                            </h3>

                            <div className="space-y-4">
                                {actions.map((action, idx) => (
                                    <div key={idx} className="bg-slate-800/50 p-4 rounded-lg border border-slate-700/50 space-y-3">
                                        <div className="flex justify-between items-center">
                                            <select
                                                value={action.name}
                                                onChange={e => { const newActions = [...actions]; newActions[idx].name = e.target.value; setActions(newActions); }}
                                                className="bg-slate-800 border border-slate-700 rounded text-sm px-3 py-1.5 text-white focus:border-blue-500 outline-none flex-1 font-mono"
                                            >
                                                {availableActions.map(a => <option key={a} value={a}>{a}</option>)}
                                            </select>
                                            <button
                                                type="button"
                                                onClick={() => setActions(actions.filter((_, i) => i !== idx))}
                                                className="p-1 px-3 text-slate-500 hover:text-red-400"
                                                disabled={actions.length === 1}
                                            >
                                                <Trash2 className="w-4 h-4" />
                                            </button>
                                        </div>
                                        <div>
                                            <label className="text-xs text-slate-500 font-mono mb-1 block">Parameters (Valid JSON Object)</label>
                                            <textarea
                                                value={action.params}
                                                onChange={e => { const newActions = [...actions]; newActions[idx].params = e.target.value; setActions(newActions); }}
                                                className="w-full bg-slate-900 border border-slate-700 rounded text-xs px-3 py-2 text-green-400 font-mono focus:border-blue-500 outline-none"
                                                rows={3}
                                                placeholder='{"message": "Hello"}'
                                            />
                                        </div>
                                    </div>
                                ))}
                            </div>
                        </div>

                    </form>
                </div>

                <div className="p-6 border-t border-slate-800 bg-slate-900 rounded-b-xl flex justify-end gap-3 sticky bottom-0 z-10">
                    <button
                        type="button" onClick={onClose}
                        className="px-4 py-2 rounded-lg text-sm font-medium text-slate-300 hover:text-white hover:bg-slate-800 transition-colors"
                    >
                        Cancel
                    </button>
                    <button
                        type="submit" form="playbook-form" disabled={isSubmitting || triggerSeverities.length === 0}
                        className="px-6 py-2 rounded-lg text-sm font-medium text-white bg-blue-600 hover:bg-blue-500 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                    >
                        {isSubmitting ? 'Saving...' : 'Save Playbook'}
                    </button>
                </div>
            </div>
        </div>
    );
}

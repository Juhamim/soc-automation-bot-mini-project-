import { useEffect, useRef } from 'react';
import { useAuth } from '../context/AuthContext';
import { toast } from 'sonner';

// Deriving the WS URL from the standard HTTP endpoint
const httpUrl = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000/api/v1";
const wsUrl = httpUrl.replace('http://', 'ws://').replace('https://', 'wss://') + '/ws/alerts';

export const useWebSocket = () => {
    const { token, user } = useAuth();
    const ws = useRef<WebSocket | null>(null);

    useEffect(() => {
        if (!token || !user) return; // Only connect if authenticated

        const connect = () => {
            ws.current = new WebSocket(wsUrl);

            ws.current.onopen = () => {
                console.log('✅ Connected to SOC WebSocket Stream');
            };

            ws.current.onmessage = (event) => {
                try {
                    const data = JSON.parse(event.data);

                    if (data.event === 'alert_processed') {
                        // Display a toast using Sonner
                        toast.info(data.msg || `Alert processed`, {
                            description: `Alert ID: ${data.alert_id.substring(0, 8)}...`,
                            action: {
                                label: 'View',
                                onClick: () => window.location.href = '/alerts'
                            }
                        });
                    }
                } catch (err) {
                    console.error('❌ Failed to parse WebSocket message', err);
                }
            };

            ws.current.onerror = (error) => {
                console.error('❌ WebSocket error:', error);
            };

            ws.current.onclose = () => {
                console.log('⚠️ WebSocket disconnected. Reconnecting in 5s...');
                // Simple reconnect mechanism
                setTimeout(connect, 5000);
            };
        };

        connect();

        return () => {
            if (ws.current) {
                ws.current.onclose = null; // Prevent reconnect loop on unmount
                ws.current.close();
            }
        };
    }, [token, user]);

    return ws.current;
};

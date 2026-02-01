import { useState, useEffect, useCallback } from 'react';

/**
 * Custom hook to manage real-time chart data
 * Maintains a 24-hour rolling window of events grouped by hour
 */
const useChartData = (events = []) => {
    const [chartData, setChartData] = useState([]);

    // Initialize 24-hour window
    const initializeChartData = useCallback(() => {
        const data = [];
        const now = new Date();

        // Create 24 hourly buckets
        for (let i = 23; i >= 0; i--) {
            const hour = new Date(now);
            hour.setHours(hour.getHours() - i, 0, 0, 0);

            data.push({
                hour: hour.toISOString(),
                label: hour.toLocaleTimeString('en-US', {
                    hour: '2-digit',
                    hour12: false
                }),
                websocket: 0,
                tickets: 0,
                webhooks: 0,
                total: 0
            });
        }

        return data;
    }, []);

    // Group events into hourly buckets
    const groupEventsByHour = useCallback((events, chartData) => {
        const updatedData = [...chartData];

        events.forEach(event => {
            const eventTime = new Date(event.timestamp);
            const eventHour = new Date(eventTime);
            eventHour.setMinutes(0, 0, 0);
            const eventHourISO = eventHour.toISOString();

            // Find the matching hour bucket
            const bucketIndex = updatedData.findIndex(bucket => bucket.hour === eventHourISO);

            if (bucketIndex !== -1) {
                // Determine event type
                const source = event.source?.toLowerCase() || '';

                if (source === 'ticket' || event.event_type === 'ticket') {
                    updatedData[bucketIndex].tickets++;
                } else if (source === 'webhook') {
                    updatedData[bucketIndex].webhooks++;
                } else {
                    updatedData[bucketIndex].websocket++;
                }

                updatedData[bucketIndex].total++;
            }
        });

        return updatedData;
    }, []);

    // Update chart data when events change
    useEffect(() => {
        const initialData = initializeChartData();
        const updatedData = groupEventsByHour(events, initialData);
        setChartData(updatedData);
    }, [events, initializeChartData, groupEventsByHour]);

    // Add a single new event to chart data
    const addEvent = useCallback((event) => {
        if (!event || !event.timestamp) {
            console.warn('Skipping chart update for invalid event:', event);
            return;
        }

        setChartData(prevData => {
            const eventTime = new Date(event.timestamp);
            if (isNaN(eventTime.getTime())) return prevData; // Invalid date check

            const eventHour = new Date(eventTime);
            eventHour.setMinutes(0, 0, 0);
            const eventHourISO = eventHour.toISOString();

            const updatedData = [...prevData];
            const bucketIndex = updatedData.findIndex(bucket => bucket.hour === eventHourISO);

            if (bucketIndex !== -1) {
                // Create a copy of the bucket to avoid mutating read-only state
                updatedData[bucketIndex] = { ...updatedData[bucketIndex] };

                const source = event.source?.toLowerCase() || '';

                // Debug log for classification
                if (source === 'ticket') {
                    console.log('Processing TICKET event:', event);
                } else if (source === '') {
                    console.warn('Event missing source:', event);
                }

                if (source === 'ticket' || event.event_type === 'ticket') {
                    updatedData[bucketIndex].tickets++;
                } else if (source === 'webhook') {
                    updatedData[bucketIndex].webhooks++;
                } else {
                    updatedData[bucketIndex].websocket++;
                }

                updatedData[bucketIndex].total++;
            }

            return updatedData;
        });
    }, []);

    // Shift the window forward by one hour (for real-time updates)
    const shiftWindow = useCallback(() => {
        setChartData(prevData => {
            const newData = [...prevData.slice(1)];
            const now = new Date();
            const newHour = new Date(now);
            newHour.setMinutes(0, 0, 0);

            newData.push({
                hour: newHour.toISOString(),
                label: newHour.toLocaleTimeString('en-US', {
                    hour: '2-digit',
                    hour12: false
                }),
                websocket: 0,
                tickets: 0,
                webhooks: 0,
                total: 0
            });

            return newData;
        });
    }, []);

    return {
        chartData,
        addEvent,
        shiftWindow
    };
};

export default useChartData;

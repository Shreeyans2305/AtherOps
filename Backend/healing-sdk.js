// healing-sdk.js - Merchant-side error tracking
(function() {
    'use strict';
    
    class HealingSDK {
        constructor(config) {
            this.apiUrl = config.apiUrl || 'ws://localhost:8000/ws/sdk';
            this.merchantId = config.merchantId;
            this.ws = null;
            this.buffer = [];
            this.init();
        }
        
        init() {
            console.log('[HealingSDK] Initializing for merchant:', this.merchantId);
            
            // Connect to backend via WebSocket
            this.connect();
            
            // Monitor JavaScript errors
            this.captureErrors();
            
            // Monitor API calls
            this.captureAPIFailures();
            
            // Monitor performance
            this.capturePerformance();
            
            // Custom events
            this.setupCustomTracking();
        }
        
        connect() {
            try {
                this.ws = new WebSocket(this.apiUrl);
                
                this.ws.onopen = () => {
                    console.log('[HealingSDK] ✅ Connected to healing platform');
                    // Send any buffered events
                    this.buffer.forEach(event => this.send(event));
                    this.buffer = [];
                };
                
                this.ws.onerror = (error) => {
                    console.error('[HealingSDK] ❌ Connection error:', error);
                };
                
                this.ws.onclose = () => {
                    console.log('[HealingSDK] Connection closed, reconnecting...');
                    setTimeout(() => this.connect(), 5000);
                };
            } catch (error) {
                console.error('[HealingSDK] Failed to connect:', error);
            }
        }
        
        send(event) {
            const signal = {
                merchant_id: this.merchantId,
                timestamp: new Date().toISOString(),
                ...event
            };
            
            if (this.ws && this.ws.readyState === WebSocket.OPEN) {
                this.ws.send(JSON.stringify(signal));
            } else {
                // Buffer if not connected
                this.buffer.push(event);
            }
        }
        
        captureErrors() {
            // Global error handler
            window.addEventListener('error', (event) => {
                this.send({
                    type: 'javascript_error',
                    severity: 'high',
                    message: event.message,
                    stack: event.error?.stack || '',
                    filename: event.filename,
                    line: event.lineno,
                    column: event.colno
                });
            });
            
            // Promise rejection handler
            window.addEventListener('unhandledrejection', (event) => {
                this.send({
                    type: 'promise_rejection',
                    severity: 'medium',
                    message: event.reason?.message || String(event.reason),
                    stack: event.reason?.stack || ''
                });
            });
        }
        
        captureAPIFailures() {
            // Intercept fetch
            const originalFetch = window.fetch;
            window.fetch = (...args) => {
                const startTime = Date.now();
                return originalFetch(...args)
                    .then(response => {
                        const duration = Date.now() - startTime;
                        
                        // Log slow or failed API calls
                        if (!response.ok || duration > 3000) {
                            this.send({
                                type: 'api_call',
                                severity: response.ok ? 'medium' : 'high',
                                message: `API ${response.ok ? 'slow' : 'failed'}: ${args[0]}`,
                                url: args[0],
                                status: response.status,
                                duration: duration
                            });
                        }
                        
                        return response;
                    })
                    .catch(error => {
                        this.send({
                            type: 'api_error',
                            severity: 'high',
                            message: `Network error: ${error.message}`,
                            url: args[0]
                        });
                        throw error;
                    });
            };
            
            // Intercept XMLHttpRequest
            const originalOpen = XMLHttpRequest.prototype.open;
            const originalSend = XMLHttpRequest.prototype.send;
            
            XMLHttpRequest.prototype.open = function(method, url) {
                this._healingUrl = url;
                this._healingMethod = method;
                this._healingStartTime = Date.now();
                return originalOpen.apply(this, arguments);
            };
            
            XMLHttpRequest.prototype.send = function() {
                this.addEventListener('load', function() {
                    const duration = Date.now() - this._healingStartTime;
                    if (this.status >= 400) {
                        window.HealingSDK.instance.send({
                            type: 'xhr_error',
                            severity: 'high',
                            message: `XHR failed: ${this._healingMethod} ${this._healingUrl}`,
                            url: this._healingUrl,
                            status: this.status,
                            duration: duration
                        });
                    }
                });
                return originalSend.apply(this, arguments);
            };
        }
        
        capturePerformance() {
            // Track page load performance
            window.addEventListener('load', () => {
                setTimeout(() => {
                    const perfData = window.performance.timing;
                    const pageLoadTime = perfData.loadEventEnd - perfData.navigationStart;
                    
                    if (pageLoadTime > 5000) {
                        this.send({
                            type: 'performance',
                            severity: 'low',
                            message: `Slow page load: ${pageLoadTime}ms`,
                            duration: pageLoadTime
                        });
                    }
                }, 0);
            });
        }
        
        setupCustomTracking() {
            // Custom event: checkout abandonment
            window.trackCheckout = (stage, data = {}) => {
                this.send({
                    type: 'checkout_event',
                    severity: 'medium',
                    message: `Checkout ${stage}`,
                    stage: stage,
                    ...data
                });
            };
            
            // Custom event: payment failure
            window.trackPaymentFailure = (error) => {
                this.send({
                    type: 'payment_failure',
                    severity: 'critical',
                    message: error.message || 'Payment failed',
                    error_code: error.code,
                    gateway: error.gateway
                });
            };
        }
    }
    
    // Auto-initialize if config exists
    if (window.HealingSDKConfig) {
        window.HealingSDK = {
            instance: new HealingSDK(window.HealingSDKConfig)
        };
    }
})();
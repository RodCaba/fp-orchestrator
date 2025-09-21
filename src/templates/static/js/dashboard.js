class HARDashboard {
    constructor() {
        this.ws = null;
        this.activities = [];
        this.currentActivity = null;
        this.sessionStartTime = null;
        this.currentMode = 'recording';
        this.predictionActive = false;
        this.stats = {
            totalBatches: 0,
            s3Uploads: 0,
            errorCount: 0
        };
        this.s3Stats = {
            totalUploads: 0,
            totalErrors: 0,
            pendingUploads: 0,
            lastUploadTime: null
        };
        
        this.init();
    }

    async init() {
        await this.loadActivities();
        this.setupEventListeners();
        this.connectWebSocket();
        this.startStatsTimer();
    }

    // WebSocket Connection
    connectWebSocket() {
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const wsUrl = `${protocol}//${window.location.host}/ws`;
        
        this.ws = new WebSocket(wsUrl);
        
        this.ws.onopen = () => {
            console.log('WebSocket connected');
            this.updateOrchestratorStatus('connected', 'Connected');
            this.showToast('Connected to orchestrator', 'success');
        };

        this.ws.onmessage = (event) => {
            const data = JSON.parse(event.data);
            this.handleWebSocketMessage(data);
        };

        this.ws.onclose = () => {
            console.log('WebSocket disconnected');
            this.updateOrchestratorStatus('error', 'Disconnected');
            this.showToast('Disconnected from orchestrator', 'error');
            
            // Reconnect after 3 seconds
            setTimeout(() => this.connectWebSocket(), 3000);
        };

        this.ws.onerror = (error) => {
            console.error('WebSocket error:', error);
            this.showToast('Connection error', 'error');
        };
    }

    // Handle incoming WebSocket messages
    handleWebSocketMessage(data) {
        switch (data.type) {
            case 'sensor_status':
                this.updateSensorStatus(data.sensor_type, data.status, data.data);
                break;
            case 'activity_update':
                this.handleActivityUpdate(data);
                break;
            case 'stats_update':
                this.updateStats(data.stats);
                break;
            case 's3_stats_update':
                this.updateS3Stats(data.stats);
                break;
            case 'orchestrator_status':
                this.updateOrchestratorStatus(data.status, data.message);
                break;
            case 'prediction_status':
                console.log('Received prediction_status:', data.data);
                this.updatePredictionStatus(data.data);
                break;
            case 'prediction_result':
                console.log('Received prediction_result:', data.data);
                this.updatePredictionResult(data.data);
                break;
            case 'prediction_progress':
                this.updatePredictionProgress(data.data.progress);
                break;
            default:
                console.log('Unknown message type:', data.type);
        }
    }

    // Activity Management
    async loadActivities() {
        try {
            const response = await fetch('/api/activities');
            if (response.ok) {
                this.activities = await response.json();
                this.populateActivitySelector();
            }
        } catch (error) {
            console.error('Error loading activities:', error);
            this.showToast('Error loading activities', 'error');
        }
    }

    async addActivity(name, description = '') {
        if (!name.trim()) {
            this.showToast('Activity name cannot be empty', 'warning');
            return;
        }

        if (this.activities.find(a => a.name.toLowerCase() === name.toLowerCase())) {
            this.showToast('Activity already exists', 'warning');
            return;
        }

        try {
            const response = await fetch('/api/activities', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ name: name.trim(), description: description.trim() })
            });

            if (response.ok) {
                const newActivity = await response.json();
                this.activities.push(newActivity);
                this.populateActivitySelector();
                this.showToast(`Activity "${name}" added successfully`, 'success');
                
                // Clear input
                document.getElementById('new-activity-input').value = '';
                document.getElementById('new-activity-description').value = '';
            } else {
                this.showToast('Error adding activity', 'error');
            }
        } catch (error) {
            console.error('Error adding activity:', error);
            this.showToast('Error adding activity', 'error');
        }
    }

    async startActivity(activityName) {
        const activity = this.activities.find(a => a.name === activityName);
        if (!activity) {
            this.showToast('Activity not found', 'error');
            return;
        }

        try {
            const response = await fetch('/api/start_activity', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ activity_name: activityName })
            });

            if (response.ok) {
                this.currentActivity = activity;
                this.updateActivityDisplay();
                this.sessionStartTime = new Date();
                this.updateOrchestratorStatus('ready', 'Ready - Recording Activity');
                this.showToast(`Started recording: ${activity.name}`, 'success');
            } else {
                this.showToast('Error starting activity', 'error');
            }
        } catch (error) {
            console.error('Error starting activity:', error);
            this.showToast('Error starting activity', 'error');
        }
    }

    async stopActivity() {
        if (!this.currentActivity) return;

        try {
            const response = await fetch('/api/stop_activity', {
                method: 'POST'
            });

            if (response.ok) {
                this.showToast(`Stopped recording`, 'success');
                this.updateActivityDisplay();
                this.updateOrchestratorStatus('connected', 'Connected - Waiting for Activity');
            } else {
                this.showToast('Error stopping activity', 'error');
            }
        } catch (error) {
            console.error('Error stopping activity:', error);
            this.showToast('Error stopping activity', 'error');
        }
    }

    // Prediction Mode Methods
    async startPrediction() {
        try {
            const response = await fetch('/api/start_prediction', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({})
            });

            if (response.ok) {
                this.predictionActive = true;
                this.updatePredictionControls();
                this.updatePredictionState('waiting', 'Loading...');
                this.showToast('Prediction mode started', 'success');
            } else {
                const error = await response.text();
                this.showToast(`Error starting prediction: ${error}`, 'error');
            }
        } catch (error) {
            console.error('Error starting prediction:', error);
            this.showToast('Error starting prediction', 'error');
        }
    }

    async stopPrediction() {
        try {
            const response = await fetch('/api/stop_prediction', {
                method: 'POST'
            });

            if (response.ok) {
                this.predictionActive = false;
                this.updatePredictionControls();
                this.updatePredictionState('inactive', 'Ready to start');
                this.hidePredictionProgress();
                this.clearPredictionResult();
                this.showToast('Prediction mode stopped', 'success');
            } else {
                const error = await response.text();
                this.showToast(`Error stopping prediction: ${error}`, 'error');
            }
        } catch (error) {
            console.error('Error stopping prediction:', error);
            this.showToast('Error stopping prediction', 'error');
        }
    }

    // UI Updates
    populateActivitySelector() {
        const selector = document.getElementById('activity-selector');
        selector.innerHTML = '<option value="">Choose an activity...</option>';
        
        this.activities.forEach(activity => {
            const option = document.createElement('option');
            option.value = activity.name;
            option.textContent = activity.name;
            selector.appendChild(option);
        });
    }

    updateActivityDisplay() {
        const label = document.getElementById('current-activity-label');
        const stopBtn = document.getElementById('stop-activity-btn');

        if (this.currentActivity) {
            label.textContent = this.currentActivity.name;
            label.classList.add('active');
            stopBtn.style.display = 'flex';
        } else {
            label.textContent = 'No activity selected';
            label.classList.remove('active');
            stopBtn.style.display = 'none';
        }
    }

    updateSensorStatus(sensorType, status, data = {}) {
        const sensorCard = document.getElementById(`${sensorType}-sensor`);
        const statusDot = sensorCard.querySelector('.status-dot');
        const statusText = sensorCard.querySelector('.status-text');

        // Update status
        statusDot.className = 'status-dot';
        if (status === 'connected') {
            statusDot.classList.add('connected');
            statusText.textContent = 'Connected';
            sensorCard.classList.add('connected');
        } else {
            statusText.textContent = 'Disconnected';
            sensorCard.classList.remove('connected');
        }

        // Update sensor-specific data
        if (sensorType === 'rfid' && data.last_signal) {
            document.getElementById('rfid-last-signal').textContent = data.last_signal;
            document.getElementById('rfid-current-users').textContent = data.current_users || 0;
        } else if (sensorType === 'imu' && data.batches_received !== undefined) {
            document.getElementById('imu-batches').textContent = data.batches_received;
        } else if (sensorType === 'audio' && data.features_processed !== undefined) {
            document.getElementById('audio-features').textContent = data.features_processed;
        }
    }

    updateOrchestratorStatus(status, message) {
        const statusIndicator = document.getElementById('orchestrator-status');
        const statusDot = statusIndicator.querySelector('.status-dot');
        const statusText = statusIndicator.querySelector('.status-text');

        statusDot.className = 'status-dot';
        statusDot.classList.add(status);
        statusText.textContent = message;
    }

    updateStats(stats) {
        Object.assign(this.stats, stats);
        
        document.getElementById('total-batches').textContent = this.stats.totalBatches;
    }

    updateS3Stats(stats) {
        Object.assign(this.s3Stats, stats);
        document.getElementById('s3-uploads').textContent = this.s3Stats.totalUploads;
        document.getElementById('error-count').textContent = this.s3Stats.totalErrors;
    }

    // Mode switching
    switchMode(mode) {
        this.currentMode = mode;
        const recordingSection = document.getElementById('recording-section');
        const predictionSection = document.getElementById('prediction-section');

        if (mode === 'recording') {
            recordingSection.style.display = 'block';
            predictionSection.style.display = 'none';
            
            // Stop prediction if active
            if (this.predictionActive) {
                this.stopPrediction();
            }
        } else if (mode === 'prediction') {
            recordingSection.style.display = 'none';
            predictionSection.style.display = 'block';
            
            // Stop activity recording if active
            if (this.currentActivity) {
                this.stopActivity();
            }
        }
    }

    // Prediction UI Updates
    updatePredictionControls() {
        const startBtn = document.getElementById('start-prediction-btn');
        const stopBtn = document.getElementById('stop-prediction-btn');

        if (this.predictionActive) {
            startBtn.style.display = 'none';
            stopBtn.style.display = 'flex';
        } else {
            startBtn.style.display = 'flex';
            stopBtn.style.display = 'none';
        }
    }

    updatePredictionState(state, text) {
        const indicator = document.getElementById('prediction-state-indicator');
        const stateText = document.getElementById('prediction-state-text');

        indicator.className = 'state-indicator';
        indicator.classList.add(state);
        stateText.textContent = text;
    }

    updatePredictionStatus(data) {
        if (data.is_active) {
            this.predictionActive = true;
            this.updatePredictionControls();
            
            if (data.waiting_for_rfid) {
                this.updatePredictionState('waiting', 'Loading...');
                this.hidePredictionProgress();
            } else if (data.collecting_data) {
                this.updatePredictionState('collecting', 'Collecting sensor data...');
                this.showPredictionProgress();
                this.updatePredictionProgress(data.data_collection_progress);
            }
            
            // Only update prediction result if there's new data, don't clear existing results
            if (data.current_prediction) {
                this.updatePredictionResult(data.current_prediction);
            }
        } else {
            this.predictionActive = false;
            this.updatePredictionControls();
            this.updatePredictionState('inactive', 'Ready to start');
            this.hidePredictionProgress();
            // Only clear prediction results when prediction mode is actually stopped
            this.clearPredictionResult();
        }
    }

    updatePredictionProgress(progress) {
        const progressFill = document.getElementById('progress-fill');
        const progressText = document.getElementById('progress-text');
        
        const percentage = Math.round(progress * 100);
        progressFill.style.width = `${percentage}%`;
        progressText.textContent = `${percentage}%`;
    }

    showPredictionProgress() {
        document.getElementById('prediction-progress').style.display = 'block';
    }

    hidePredictionProgress() {
        document.getElementById('prediction-progress').style.display = 'none';
    }

    updatePredictionResult(result) {
        console.log('updatePredictionResult called with:', result);
        const resultEmpty = document.querySelector('.result-empty');
        const resultContent = document.getElementById('prediction-result-content');
        
        resultEmpty.style.display = 'none';
        resultContent.style.display = 'block';
        
        // Update result content
        console.log('Setting predicted-activity-name to:', result.predicted_label);
        document.getElementById('predicted-activity-name').textContent = result.predicted_label;
        document.getElementById('prediction-timestamp').textContent = new Date(result.timestamp).toLocaleString();
        document.getElementById('prediction-users').textContent = result.n_users;
        
        // Update confidence badge
        const confidenceBadge = document.getElementById('confidence-badge');
        const confidence = Math.round(result.confidence * 100);
        confidenceBadge.textContent = `${confidence}%`;
        
        // Set confidence color
        confidenceBadge.className = 'confidence-badge';
        if (confidence >= 80) {
            confidenceBadge.classList.add('high');
        } else if (confidence >= 60) {
            confidenceBadge.classList.add('medium');
        } else {
            confidenceBadge.classList.add('low');
        }
        
        this.updatePredictionState('active', 'Prediction complete');
    }

    clearPredictionResult() {
        const resultEmpty = document.querySelector('.result-empty');
        const resultContent = document.getElementById('prediction-result-content');
        
        resultEmpty.style.display = 'block';
        resultContent.style.display = 'none';
    }

    // Event Listeners
    setupEventListeners() {
        // Mode switcher
        document.querySelectorAll('input[name="mode"]').forEach(radio => {
            radio.addEventListener('change', (e) => {
                this.switchMode(e.target.value);
            });
        });

        // Activity selector
        document.getElementById('activity-selector').addEventListener('change', (e) => {
            const startBtn = document.getElementById('start-activity-btn');
            startBtn.disabled = !e.target.value || this.currentActivity !== null;
        });

        // Start activity button
        document.getElementById('start-activity-btn').addEventListener('click', () => {
            const selectedId = document.getElementById('activity-selector').value;
            if (selectedId) {
                this.startActivity(selectedId);
            }
        });

        // Stop activity button
        document.getElementById('stop-activity-btn').addEventListener('click', () => {
            this.stopActivity();
        });

        // Add activity
        document.getElementById('add-activity-btn').addEventListener('click', () => {
            const name = document.getElementById('new-activity-input').value;
            const description = document.getElementById('new-activity-description').value;
            this.addActivity(name, description);
        });

        // Add activity on Enter key
        document.getElementById('new-activity-input').addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                const name = e.target.value;
                this.addActivity(name);
            }
        });

        // Prediction mode buttons
        document.getElementById('start-prediction-btn').addEventListener('click', () => {
            this.startPrediction();
        });

        document.getElementById('stop-prediction-btn').addEventListener('click', () => {
            this.stopPrediction();
        });
    }

    // Timer for session time
    startStatsTimer() {
        setInterval(() => {
            if (this.sessionStartTime) {
                const elapsed = new Date() - this.sessionStartTime;
                const hours = Math.floor(elapsed / 3600000);
                const minutes = Math.floor((elapsed % 3600000) / 60000);
                const seconds = Math.floor((elapsed % 60000) / 1000);
                
                document.getElementById('current-session-time').textContent = 
                    `${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
            } else {
                document.getElementById('current-session-time').textContent = '00:00:00';
            }
        }, 1000);
    }

    // Toast notifications
    showToast(message, type = 'info') {
        const container = document.getElementById('toast-container');
        const toast = document.createElement('div');
        toast.className = `toast ${type}`;
        
        const icon = type === 'success' ? 'fa-check-circle' : 
                    type === 'error' ? 'fa-exclamation-circle' : 
                    type === 'warning' ? 'fa-exclamation-triangle' : 'fa-info-circle';
        
        toast.innerHTML = `
            <i class="fas ${icon}"></i>
            <span>${message}</span>
        `;
        
        container.appendChild(toast);
        
        // Auto remove after 5 seconds
        setTimeout(() => {
            if (toast.parentNode) {
                toast.parentNode.removeChild(toast);
            }
        }, 5000);
    }

    // Handle activity update from backend
    handleActivityUpdate(data) {
        if (data.action === 'started') {
            const activity = this.activities.find(a => a.id === data.activity_id);
            if (activity) {
                this.currentActivity = activity;
                this.sessionStartTime = new Date();
                this.updateActivityDisplay();
            }
        } else if (data.action === 'stopped') {
            this.currentActivity = null;
            this.sessionStartTime = null;
            this.updateActivityDisplay();
        }
    }
}

// Initialize dashboard when page loads
let dashboard;
document.addEventListener('DOMContentLoaded', () => {
    dashboard = new HARDashboard();
});
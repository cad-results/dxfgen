// DXF Generator Chatbot - Frontend JavaScript

class DXFChatbot {
    constructor() {
        this.sessionId = this.generateSessionId();
        this.chatMessages = document.getElementById('chat-messages');
        this.userInput = document.getElementById('user-input');
        this.sendBtn = document.getElementById('send-btn');
        this.continueBtn = document.getElementById('continue-btn');
        this.metadataPanel = document.getElementById('metadata-panel');
        this.metadataContent = document.getElementById('metadata-content');
        this.generateBtn = document.getElementById('generate-btn');
        this.editBtn = document.getElementById('edit-btn');
        this.downloadPanel = document.getElementById('download-panel');
        this.downloadList = document.getElementById('download-list');
        this.downloadAllBtn = document.getElementById('download-all-btn');
        this.loading = document.getElementById('loading');

        this.currentMetadata = null;
        this.downloadUrl = null;
        this.dxfDownloadUrl = null;
        this.originalInput = null;
        this.refinementHistory = [];
        this.viewerAvailable = false;
        this.viewableFormats = ['.glb', '.gltf', '.obj', '.ply', '.stl', '.off'];
        this.view2dFormats = ['.dxf', '.svg'];
        this.viewer2dAvailable = true;

        // Multi-format selection
        this.selectedFormats = ['DXF'];  // DXF always included
        this.availableFormats = {};
        this.generatedFiles = {};  // Store generated file info

        // Settings elements
        this.settingsToggle = document.getElementById('settings-toggle');
        this.settingsPanel = document.getElementById('settings-panel');
        this.autoAcceptMode = document.getElementById('auto-accept-mode');
        this.includeFurniture = document.getElementById('include-furniture');
        this.includeAnnotations = document.getElementById('include-annotations');
        this.qualityLevel = document.getElementById('quality-level');
        this.refinementPasses = document.getElementById('refinement-passes');
        this.refinementValue = document.getElementById('refinement-value');
        this.saveSettingsBtn = document.getElementById('save-settings-btn');
        this.resetSettingsBtn = document.getElementById('reset-settings-btn');
        this.settingsStatus = document.getElementById('settings-status');

        // Current settings
        this.settings = this.loadSettings();

        this.setupEventListeners();
        this.applySettings();
        this.checkViewerStatus();
        this.check2DViewerStatus();
        this.loadAvailableFormats();
    }

    generateSessionId() {
        return 'session_' + Math.random().toString(36).substr(2, 9);
    }

    setupEventListeners() {
        this.sendBtn.addEventListener('click', () => this.sendMessage(false));
        this.continueBtn.addEventListener('click', () => this.sendMessage(true));
        this.userInput.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                this.sendMessage(false);
            }
        });

        this.generateBtn.addEventListener('click', () => this.generateDXF());
        this.editBtn.addEventListener('click', () => this.editMetadata());

        // Preview button in metadata panel
        const previewBtn = document.getElementById('preview-btn');
        if (previewBtn) {
            previewBtn.addEventListener('click', () => this.preview2D());
        }

        // 2D viewer modal controls
        this.setup2DViewerControls();

        // Settings event listeners
        this.settingsToggle.addEventListener('click', () => this.toggleSettings());
        this.saveSettingsBtn.addEventListener('click', () => this.saveSettings());
        this.resetSettingsBtn.addEventListener('click', () => this.resetSettings());
        this.refinementPasses.addEventListener('input', (e) => {
            this.refinementValue.textContent = e.target.value;
        });
    }

    loadSettings() {
        // Load from localStorage or use defaults
        const stored = localStorage.getItem('dxf_settings');
        if (stored) {
            return JSON.parse(stored);
        }
        return {
            auto_accept_mode: false,
            include_furniture: false,
            include_annotations: true,
            quality_level: 'professional',
            refinement_passes: 3
        };
    }

    applySettings() {
        // Apply settings to UI
        this.autoAcceptMode.checked = this.settings.auto_accept_mode;
        this.includeFurniture.checked = this.settings.include_furniture;
        this.includeAnnotations.checked = this.settings.include_annotations;
        this.qualityLevel.value = this.settings.quality_level;
        this.refinementPasses.value = this.settings.refinement_passes;
        this.refinementValue.textContent = this.settings.refinement_passes;
    }

    toggleSettings() {
        if (this.settingsPanel.style.display === 'none') {
            this.settingsPanel.style.display = 'block';
        } else {
            this.settingsPanel.style.display = 'none';
        }
    }

    async saveSettings() {
        // Read settings from UI
        this.settings = {
            auto_accept_mode: this.autoAcceptMode.checked,
            include_furniture: this.includeFurniture.checked,
            include_annotations: this.includeAnnotations.checked,
            quality_level: this.qualityLevel.value,
            refinement_passes: parseInt(this.refinementPasses.value)
        };

        // Save to localStorage
        localStorage.setItem('dxf_settings', JSON.stringify(this.settings));

        // Show status message
        this.showSettingsStatus('Settings saved successfully!', 'success');

        // Send to backend
        try {
            await fetch('/api/settings', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    session_id: this.sessionId,
                    settings: this.settings
                })
            });
        } catch (error) {
            console.error('Error saving settings to server:', error);
        }
    }

    async resetSettings() {
        // Reset to defaults
        this.settings = {
            auto_accept_mode: false,
            include_furniture: false,
            include_annotations: true,
            quality_level: 'professional',
            refinement_passes: 3
        };

        // Apply to UI
        this.applySettings();

        // Save to localStorage
        localStorage.setItem('dxf_settings', JSON.stringify(this.settings));

        // Show status message
        this.showSettingsStatus('Settings reset to defaults!', 'success');

        // Send to backend
        try {
            await fetch('/api/settings/reset', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    session_id: this.sessionId
                })
            });
        } catch (error) {
            console.error('Error resetting settings on server:', error);
        }
    }

    showSettingsStatus(message, type) {
        this.settingsStatus.textContent = message;
        this.settingsStatus.className = `settings-status ${type}`;
        this.settingsStatus.style.display = 'block';

        // Hide after 3 seconds
        setTimeout(() => {
            this.settingsStatus.style.display = 'none';
        }, 3000);
    }

    async loadAvailableFormats() {
        try {
            const response = await fetch('/api/formats');
            const data = await response.json();
            this.availableFormats = data.categories || {};
            this.renderFormatToggles();
        } catch (error) {
            console.error('Error loading formats:', error);
            // Use default formats if API fails
            this.renderDefaultFormatToggles();
        }
    }

    renderFormatToggles() {
        // Render 3D CAD formats
        const cad3dContainer = document.getElementById('formats-3d-cad');
        if (cad3dContainer && this.availableFormats['3d_cad']) {
            cad3dContainer.innerHTML = this.renderFormatCategory(this.availableFormats['3d_cad'].formats);
        }

        // Render 2D export formats
        const export2dContainer = document.getElementById('formats-2d-export');
        if (export2dContainer && this.availableFormats['2d_export']) {
            export2dContainer.innerHTML = this.renderFormatCategory(this.availableFormats['2d_export'].formats);
        }

        // Render DWG format
        const dwgContainer = document.getElementById('formats-dwg');
        if (dwgContainer && this.availableFormats['dwg']) {
            dwgContainer.innerHTML = this.renderFormatCategory(this.availableFormats['dwg'].formats);
        }

        // Add event listeners to all format toggles
        document.querySelectorAll('.format-toggle input[type="checkbox"]:not([disabled])').forEach(checkbox => {
            checkbox.addEventListener('change', (e) => this.handleFormatToggle(e.target.value, e.target.checked));
        });
    }

    renderFormatCategory(formats) {
        return formats.map(fmt => {
            const isAvailable = fmt.available;
            const disabledClass = isAvailable ? '' : 'unavailable';
            const disabledAttr = isAvailable ? '' : 'disabled';
            const tooltip = !isAvailable && fmt.reason ? `title="${fmt.reason}"` : '';

            return `
                <div class="format-toggle ${disabledClass}" ${tooltip}>
                    <input type="checkbox" id="fmt-${fmt.name}" value="${fmt.name}" ${disabledAttr}>
                    <label for="fmt-${fmt.name}">
                        <span class="format-name">${fmt.name}</span>
                        <span class="format-desc">${fmt.description}</span>
                        ${!isAvailable ? '<span class="format-unavailable-badge">Not Available</span>' : ''}
                    </label>
                </div>
            `;
        }).join('');
    }

    renderDefaultFormatToggles() {
        // Fallback if API fails
        const defaultFormats = {
            '3d_cad': [
                { name: 'STEP', description: 'Industry Standard CAD Exchange', available: true },
                { name: 'IGES', description: 'Legacy CAD Exchange', available: true },
                { name: 'STL', description: '3D Printing / Mesh', available: true },
                { name: 'OBJ', description: '3D Modeling / Mesh', available: true },
                { name: 'GLTF', description: 'Web 3D / AR/VR', available: true },
                { name: 'PLY', description: 'Point Cloud / Mesh', available: true },
            ],
            '2d_export': [
                { name: 'PDF', description: 'Documentation / Print', available: false, reason: 'Check ezdxf drawing addon' },
                { name: 'SVG', description: 'Web Graphics / Vector', available: false, reason: 'Check ezdxf drawing addon' },
                { name: 'PNG', description: 'Preview Image / Raster', available: false, reason: 'Check ezdxf drawing addon' },
            ],
            'dwg': [
                { name: 'DWG', description: 'AutoCAD Native Format', available: false, reason: 'ODA File Converter not installed' }
            ]
        };

        const cad3dContainer = document.getElementById('formats-3d-cad');
        if (cad3dContainer) {
            cad3dContainer.innerHTML = this.renderFormatCategory(defaultFormats['3d_cad']);
        }

        const export2dContainer = document.getElementById('formats-2d-export');
        if (export2dContainer) {
            export2dContainer.innerHTML = this.renderFormatCategory(defaultFormats['2d_export']);
        }

        const dwgContainer = document.getElementById('formats-dwg');
        if (dwgContainer) {
            dwgContainer.innerHTML = this.renderFormatCategory(defaultFormats['dwg']);
        }

        // Add event listeners
        document.querySelectorAll('.format-toggle input[type="checkbox"]:not([disabled])').forEach(checkbox => {
            checkbox.addEventListener('change', (e) => this.handleFormatToggle(e.target.value, e.target.checked));
        });
    }

    handleFormatToggle(format, checked) {
        if (checked) {
            if (!this.selectedFormats.includes(format)) {
                this.selectedFormats.push(format);
            }
        } else {
            const index = this.selectedFormats.indexOf(format);
            if (index > -1 && format !== 'DXF') {  // Never remove DXF
                this.selectedFormats.splice(index, 1);
            }
        }
        // Update generate button text based on selection count
        const formatCount = this.selectedFormats.length;
        this.generateBtn.textContent = formatCount > 1 ? `Generate ${formatCount} Files` : 'Generate File';
    }

    async sendMessage(isContinuation = false) {
        const message = this.userInput.value.trim();
        if (!message) return;

        // Add user message to chat
        this.addMessage('user', message);
        this.userInput.value = '';
        this.sendBtn.disabled = true;
        this.continueBtn.disabled = true;
        this.showLoading();

        try {
            // Build request payload
            const payload = {
                message: message,
                session_id: this.sessionId,
                settings: this.settings
            };

            // If this is a continuation, include context
            if (isContinuation && this.originalInput && this.currentMetadata) {
                payload.is_refinement = true;
                payload.refinement_context = {
                    original_input: this.originalInput,
                    previous_metadata: this.currentMetadata,
                    refinement_history: this.refinementHistory
                };

                // Add to refinement history
                this.refinementHistory.push(message);
            } else {
                // Store as original input for potential refinements
                this.originalInput = message;
                this.refinementHistory = [];
            }

            const response = await fetch('/api/chat', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(payload)
            });

            const data = await response.json();

            if (response.ok) {
                // Add assistant messages (skip user messages as we already added them)
                const newMessages = data.messages.filter(msg => msg.role === 'assistant');
                for (const msg of newMessages) {
                    // Skip the first message if it's already in the chat
                    this.addMessage('assistant', msg.content);
                }

                // Check if conversation is complete and we can generate
                if (data.can_generate && data.csv_metadata) {
                    this.currentMetadata = data.csv_metadata;
                    this.showMetadataPanel();
                    // Show Continue button for refinement
                    this.continueBtn.style.display = 'inline-block';
                    // Update placeholder for refinement
                    this.userInput.placeholder = 'Add more details to refine the metadata...';
                }

            } else {
                this.addMessage('assistant', `Error: ${data.error}`);
            }

        } catch (error) {
            console.error('Error:', error);
            this.addMessage('assistant', 'Sorry, an error occurred. Please try again.');
        } finally {
            this.hideLoading();
            this.sendBtn.disabled = false;
            this.continueBtn.disabled = false;
            this.scrollToBottom();
        }
    }

    async checkViewerStatus() {
        try {
            const response = await fetch('/api/viewer/status');
            const data = await response.json();
            this.viewerAvailable = data.available || data.fallback_available;
            this.viewerDetails = data.details || {};
            this.viewableFormats = data.supported_formats || this.viewableFormats;
        } catch (error) {
            this.viewerAvailable = false;
            this.viewerDetails = {};
        }
    }

    async check2DViewerStatus() {
        try {
            const response = await fetch('/api/viewer/2d-status');
            const data = await response.json();
            this.viewer2dAvailable = data.available;
            this.view2dFormats = data.supported_formats || this.view2dFormats;
        } catch (error) {
            this.viewer2dAvailable = true; // SVG generation should always work
        }
    }

    setup2DViewerControls() {
        // Close modal button
        const modal = document.getElementById('viewer-2d-modal');
        if (!modal) return;

        const closeBtn = modal.querySelector('.modal-close');
        if (closeBtn) {
            closeBtn.addEventListener('click', () => this.close2DViewer());
        }

        // Close on background click
        modal.addEventListener('click', (e) => {
            if (e.target === modal) {
                this.close2DViewer();
            }
        });

        // Zoom controls
        const zoomIn = document.getElementById('zoom-in-2d');
        const zoomOut = document.getElementById('zoom-out-2d');
        const resetView = document.getElementById('reset-view-2d');
        const openExternal = document.getElementById('open-external-2d');

        if (zoomIn) zoomIn.addEventListener('click', () => this.zoom2D(1.2));
        if (zoomOut) zoomOut.addEventListener('click', () => this.zoom2D(0.8));
        if (resetView) resetView.addEventListener('click', () => this.reset2DView());
        if (openExternal) openExternal.addEventListener('click', () => this.openExternal2D());

        // Track current zoom level and file
        this.viewer2dZoom = 1;
        this.viewer2dCurrentFile = null;
    }

    async view2DFile(filename, openExternal = false) {
        try {
            this.showLoading();

            const response = await fetch('/api/view-2d', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ filename, open_external: openExternal })
            });

            const data = await response.json();

            if (data.success) {
                if (openExternal) {
                    this.addMessage('assistant', `2D viewer launched for ${filename}`);
                } else {
                    this.show2DViewer(data.svg, filename);
                }
            } else {
                this.addMessage('assistant', `Could not view file: ${data.error}`);
            }
        } catch (error) {
            console.error('Error viewing 2D file:', error);
            this.addMessage('assistant', 'Error launching 2D viewer.');
        } finally {
            this.hideLoading();
        }
    }

    async preview2D() {
        if (!this.currentMetadata) {
            this.addMessage('assistant', 'No metadata available for preview.');
            return;
        }

        try {
            this.showLoading();

            const response = await fetch('/api/preview-2d', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    session_id: this.sessionId,
                    csv_metadata: this.currentMetadata
                })
            });

            const data = await response.json();

            if (data.success) {
                this.show2DViewer(data.svg, 'Metadata Preview');
            } else {
                this.addMessage('assistant', `Could not generate preview: ${data.error}`);
            }
        } catch (error) {
            console.error('Error generating preview:', error);
            this.addMessage('assistant', 'Error generating 2D preview.');
        } finally {
            this.hideLoading();
        }
    }

    show2DViewer(svgContent, title) {
        const modal = document.getElementById('viewer-2d-modal');
        const container = document.getElementById('viewer-2d-container');
        const titleEl = document.getElementById('viewer-2d-title');

        if (!modal || !container) {
            // Fallback: open SVG in new tab
            const blob = new Blob([svgContent], { type: 'image/svg+xml' });
            const url = URL.createObjectURL(blob);
            window.open(url, '_blank');
            return;
        }

        // Set title
        if (titleEl) {
            titleEl.textContent = title || '2D Viewer';
        }

        // Insert SVG
        container.innerHTML = svgContent;

        // Reset zoom
        this.viewer2dZoom = 1;
        this.viewer2dCurrentFile = title;
        this.apply2DZoom();

        // Show modal
        modal.style.display = 'flex';
    }

    close2DViewer() {
        const modal = document.getElementById('viewer-2d-modal');
        if (modal) {
            modal.style.display = 'none';
        }
    }

    zoom2D(factor) {
        this.viewer2dZoom *= factor;
        this.viewer2dZoom = Math.max(0.1, Math.min(10, this.viewer2dZoom));
        this.apply2DZoom();
    }

    reset2DView() {
        this.viewer2dZoom = 1;
        this.apply2DZoom();
    }

    apply2DZoom() {
        const container = document.getElementById('viewer-2d-container');
        if (container) {
            const svg = container.querySelector('svg');
            if (svg) {
                svg.style.transform = `scale(${this.viewer2dZoom})`;
                svg.style.transformOrigin = 'center center';
            }
        }
    }

    async openExternal2D() {
        if (!this.viewer2dCurrentFile) {
            this.addMessage('assistant', 'No file selected for external viewing.');
            return;
        }

        // If it's a preview, we can't open externally easily
        if (this.viewer2dCurrentFile === 'Metadata Preview') {
            this.addMessage('assistant', 'Preview cannot be opened externally. Generate the file first.');
            return;
        }

        try {
            const response = await fetch('/api/view-2d', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    filename: this.viewer2dCurrentFile,
                    open_external: true
                })
            });

            const data = await response.json();

            if (data.success) {
                this.addMessage('assistant', data.message);
            } else {
                this.addMessage('assistant', `Could not launch external viewer: ${data.error}`);
            }
        } catch (error) {
            console.error('Error launching external viewer:', error);
            this.addMessage('assistant', 'Error launching external viewer.');
        }
    }

    async generateDXF() {
        if (!this.currentMetadata) return;

        this.showLoading();

        try {
            const response = await fetch('/api/generate-multi', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    session_id: this.sessionId,
                    csv_metadata: this.currentMetadata,
                    formats: this.selectedFormats
                })
            });

            const data = await response.json();

            if (response.ok && data.success) {
                this.generatedFiles = {};

                // Store DXF info
                if (data.dxf) {
                    this.generatedFiles['DXF'] = {
                        success: true,
                        filename: data.dxf.filename,
                        download_url: data.dxf.download_url
                    };
                }

                // Store conversion results
                if (data.conversions) {
                    for (const [fmt, result] of Object.entries(data.conversions)) {
                        this.generatedFiles[fmt] = result;
                    }
                }

                // Render download list
                this.renderDownloadList();
                this.showDownloadPanel();

                // Show success message
                const successCount = Object.values(this.generatedFiles).filter(f => f.success).length;
                const totalCount = Object.keys(this.generatedFiles).length;
                if (successCount === totalCount) {
                    this.addMessage('assistant', `All ${successCount} files generated successfully!`);
                } else {
                    this.addMessage('assistant', `${successCount} of ${totalCount} files generated. Some conversions failed.`);
                }

            } else {
                this.addMessage('assistant', `Error generating files: ${data.error}`);
            }

        } catch (error) {
            console.error('Error:', error);
            this.addMessage('assistant', 'Sorry, an error occurred while generating files.');
        } finally {
            this.hideLoading();
        }
    }

    renderDownloadList() {
        const downloadList = this.downloadList;
        downloadList.innerHTML = '';

        // Sort formats: DXF first, then alphabetically
        const formats = Object.keys(this.generatedFiles).sort((a, b) => {
            if (a === 'DXF') return -1;
            if (b === 'DXF') return 1;
            return a.localeCompare(b);
        });

        for (const fmt of formats) {
            const file = this.generatedFiles[fmt];
            const item = document.createElement('div');
            item.className = `download-item ${file.success ? 'success' : 'error'}`;

            if (file.success) {
                const ext = '.' + file.filename.split('.').pop().toLowerCase();
                const is3DViewable = this.viewerAvailable && this.viewableFormats.includes(ext);
                const is2DViewable = this.viewer2dAvailable && this.view2dFormats.includes(ext);

                item.innerHTML = `
                    <div class="download-item-info">
                        <span class="download-status-icon">&#10003;</span>
                        <span class="download-format">${fmt}</span>
                        <span class="download-filename">${file.filename}</span>
                    </div>
                    <div class="download-item-actions">
                        ${is2DViewable ? `<button class="btn-view-2d-small" data-filename="${file.filename}">View 2D</button>` : ''}
                        ${is3DViewable ? `<button class="btn-view-small" data-filename="${file.filename}">View 3D</button>` : ''}
                        <button class="btn-download-small" data-url="${file.download_url}">Download</button>
                    </div>
                `;
            } else {
                item.innerHTML = `
                    <div class="download-item-info">
                        <span class="download-status-icon error">&#10007;</span>
                        <span class="download-format">${fmt}</span>
                        <span class="download-error">${file.error || 'Conversion failed'}</span>
                    </div>
                `;
            }

            downloadList.appendChild(item);
        }

        // Add event listeners for download and view buttons
        downloadList.querySelectorAll('.btn-download-small').forEach(btn => {
            btn.addEventListener('click', () => {
                window.location.href = btn.dataset.url;
            });
        });

        downloadList.querySelectorAll('.btn-view-small').forEach(btn => {
            btn.addEventListener('click', () => {
                this.viewFileByName(btn.dataset.filename);
            });
        });

        downloadList.querySelectorAll('.btn-view-2d-small').forEach(btn => {
            btn.addEventListener('click', () => {
                this.view2DFile(btn.dataset.filename);
            });
        });

        // Update panel title
        const successCount = Object.values(this.generatedFiles).filter(f => f.success).length;
        const title = document.getElementById('download-panel-title');
        if (title) {
            if (successCount === Object.keys(this.generatedFiles).length) {
                title.textContent = 'Files Generated Successfully!';
                title.className = '';
            } else {
                title.textContent = 'Generation Complete (with errors)';
                title.className = 'has-errors';
            }
        }
    }

    async viewFileByName(filename, useFallback = false) {
        try {
            const response = await fetch('/api/view', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ filename, use_fallback: useFallback })
            });

            const data = await response.json();

            if (response.ok && data.success) {
                const viewerType = data.fallback ? 'Fallback viewer' : '3D viewer';
                this.addMessage('assistant', `${viewerType} launched for ${filename}. Check your display for the viewer window.`);
            } else {
                let errorMsg = `Could not launch 3D viewer: ${data.error}`;

                // Provide helpful suggestions based on the error
                if (data.details) {
                    if (!data.details.display_available) {
                        errorMsg += '\n\nNote: 3D viewing requires a display with OpenGL support. In WSL2 environments, try:';
                        errorMsg += '\n- Using an X11 server (VcXsrv, X410)';
                        errorMsg += '\n- Or install meshlab/f3d for fallback viewing';
                    }
                    if (data.details.fallback_viewers && data.details.fallback_viewers.length > 0) {
                        errorMsg += `\n\nTip: Fallback viewers available: ${data.details.fallback_viewers.join(', ')}`;
                    }
                }

                // If DXF format, suggest 2D viewer
                const ext = '.' + filename.split('.').pop().toLowerCase();
                if (this.view2dFormats.includes(ext)) {
                    errorMsg += '\n\nFor DXF files, you can use the "View 2D" button instead.';
                }

                this.addMessage('assistant', errorMsg);
            }
        } catch (error) {
            console.error('Error launching viewer:', error);
            this.addMessage('assistant', 'Error launching the 3D viewer. Try using the 2D viewer for DXF files.');
        }
    }

    editMetadata() {
        const newMetadata = prompt('Edit the CSV metadata:', this.currentMetadata);
        if (newMetadata !== null) {
            this.currentMetadata = newMetadata;
            this.metadataContent.textContent = newMetadata;
        }
    }

    addMessage(role, content) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${role}`;

        const messageContent = document.createElement('div');
        messageContent.className = 'message-content';

        // Convert newlines to paragraphs and handle lists
        const paragraphs = content.split('\n').filter(p => p.trim());
        let currentList = null;

        for (const para of paragraphs) {
            if (para.trim().startsWith('-') || para.trim().startsWith('•')) {
                // List item
                if (!currentList) {
                    currentList = document.createElement('ul');
                    messageContent.appendChild(currentList);
                }
                const li = document.createElement('li');
                li.textContent = para.trim().substring(1).trim();
                currentList.appendChild(li);
            } else if (/^\d+\./.test(para.trim())) {
                // Numbered list
                if (!currentList || currentList.tagName !== 'OL') {
                    currentList = document.createElement('ol');
                    messageContent.appendChild(currentList);
                }
                const li = document.createElement('li');
                li.textContent = para.trim().replace(/^\d+\.\s*/, '');
                currentList.appendChild(li);
            } else {
                // Regular paragraph
                currentList = null;
                const p = document.createElement('p');
                p.textContent = para;
                messageContent.appendChild(p);
            }
        }

        messageDiv.appendChild(messageContent);
        this.chatMessages.appendChild(messageDiv);
    }

    showMetadataPanel() {
        this.metadataContent.textContent = this.currentMetadata;
        this.metadataPanel.style.display = 'block';
    }

    showDownloadPanel() {
        this.downloadPanel.style.display = 'block';
    }

    showLoading() {
        this.loading.style.display = 'flex';
    }

    hideLoading() {
        this.loading.style.display = 'none';
    }

    scrollToBottom() {
        this.chatMessages.scrollTop = this.chatMessages.scrollHeight;
    }
}

// Initialize chatbot when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    new DXFChatbot();
});

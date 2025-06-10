<!DOCTYPE html>
<html lang="fr" data-theme="dark">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta name="description" content="Hunter Agency Email Engine - Tableau de bord temps réel">
    
    <!-- Google Fonts -->
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
    
    <title>📧 Hunter Agency - Email Engine Dashboard</title>
    
    <style>
        /* ===== VARIABLES CSS ===== */
        :root {
            --primary-gradient-start: #0d1b2a;
            --primary-gradient-end: #1b263b;
            --card-bg: rgba(255, 255, 255, 0.05);
            --card-border: rgba(255, 255, 255, 0.1);
            --text-primary: #e1e8ed;
            --text-secondary: #94a3b8;
            --primary-color: #667eea;
            --success: #10b981;
            --warning: #f59e0b;
            --error: #ef4444;
            --info: #3b82f6;
        }

        /* ===== RESET & BASE ===== */
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: 'Inter', -apple-system, sans-serif;
            background: linear-gradient(135deg, var(--primary-gradient-start) 0%, var(--primary-gradient-end) 100%);
            background-attachment: fixed;
            min-height: 100vh;
            color: var(--text-primary);
            line-height: 1.6;
            overflow-x: hidden;
        }

        /* ===== LOADING SCREEN ===== */
        .loading-screen {
            position: fixed;
            inset: 0;
            background: var(--primary-gradient-start);
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            z-index: 9999;
            transition: opacity 0.5s ease;
        }

        .loading-screen.hidden {
            opacity: 0;
            pointer-events: none;
            display: none;
        }

        .spinner-large {
            width: 60px;
            height: 60px;
            border: 4px solid rgba(255, 255, 255, 0.1);
            border-top: 4px solid white;
            border-radius: 50%;
            animation: spin 1s linear infinite;
            margin-bottom: 20px;
        }

        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }

        /* ===== HEADER ===== */
        .dashboard-header {
            text-align: center;
            padding: 3rem 1.5rem 2rem;
            color: white;
        }

        .header-content h1 {
            font-size: 2.5rem;
            font-weight: 700;
            margin-bottom: 0.5rem;
            background: linear-gradient(135deg, #ffffff 0%, #e0e9ff 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            text-shadow: 0 2px 20px rgba(255, 255, 255, 0.1);
        }

        .header-content p {
            font-size: 1.1rem;
            opacity: 0.8;
            color: #cbd5e1;
        }

        /* ===== MODULE NAV ===== */
        .module-nav {
            display: flex;
            justify-content: center;
            gap: 0.5rem;
            margin-top: 1.5rem;
            flex-wrap: wrap;
        }

        .module-btn {
            background: rgba(255, 255, 255, 0.05);
            border: 2px solid rgba(255, 255, 255, 0.1);
            color: rgba(255, 255, 255, 0.8);
            padding: 0.5rem 1.5rem;
            border-radius: 2rem;
            font-weight: 500;
            font-size: 0.875rem;
            cursor: pointer;
            transition: all 0.3s ease;
            backdrop-filter: blur(10px);
        }

        .module-btn:hover:not(:disabled) {
            background: rgba(255, 255, 255, 0.1);
            border-color: rgba(255, 255, 255, 0.3);
            transform: translateY(-2px);
            box-shadow: 0 4px 16px rgba(255, 255, 255, 0.1);
        }

        .module-btn.active {
            background: rgba(102, 126, 234, 0.2);
            border-color: var(--primary-color);
            color: white;
        }

        .module-btn:disabled {
            opacity: 0.4;
            cursor: not-allowed;
        }

        /* ===== MAIN CONTAINER ===== */
        .main-container {
            max-width: 1400px;
            margin: 0 auto;
            padding: 0 1.5rem 3rem;
        }

        /* ===== CONTROLS SECTION ===== */
        .controls-section {
            display: flex;
            justify-content: center;
            align-items: center;
            gap: 1.5rem;
            margin-bottom: 2rem;
            flex-wrap: wrap;
        }

        .control-group {
            display: flex;
            gap: 0.5rem;
            align-items: center;
        }

        /* ===== BUTTONS ===== */
        .btn {
            background: rgba(255, 255, 255, 0.08);
            color: white;
            border: 1px solid rgba(255, 255, 255, 0.2);
            padding: 0.6rem 1.2rem;
            border-radius: 0.5rem;
            font-weight: 500;
            font-size: 0.875rem;
            cursor: pointer;
            transition: all 0.3s ease;
            backdrop-filter: blur(10px);
            display: flex;
            align-items: center;
            gap: 0.5rem;
            text-decoration: none;
            position: relative;
            overflow: hidden;
        }

        .btn:hover {
            background: rgba(255, 255, 255, 0.15);
            border-color: rgba(255, 255, 255, 0.4);
            transform: translateY(-2px);
            box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3);
        }

        .btn.active {
            background: var(--primary-color);
            border-color: var(--primary-color);
            color: white;
            box-shadow: 0 4px 20px rgba(102, 126, 234, 0.4);
        }

        .btn:disabled {
            opacity: 0.5;
            cursor: not-allowed;
        }

        /* ===== THEME TOGGLE ===== */
        .theme-toggle {
            background: rgba(255, 255, 255, 0.08);
            border: 1px solid rgba(255, 255, 255, 0.2);
            color: white;
            padding: 0.6rem;
            border-radius: 50%;
            width: 44px;
            height: 44px;
            display: flex;
            align-items: center;
            justify-content: center;
            cursor: pointer;
            transition: all 0.3s ease;
            font-size: 1.2rem;
        }

        .theme-toggle:hover {
            background: rgba(255, 255, 255, 0.15);
            transform: rotate(15deg) scale(1.1);
        }

        /* ===== SELECT ===== */
        .language-select {
            background: rgba(255, 255, 255, 0.08);
            color: white;
            border: 1px solid rgba(255, 255, 255, 0.2);
            padding: 0.6rem 1rem;
            border-radius: 0.5rem;
            font-weight: 500;
            font-size: 0.875rem;
            cursor: pointer;
            backdrop-filter: blur(10px);
        }

        .language-select option {
            background: #1a1a2e;
        }

        /* ===== STATS GRID ===== */
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
            gap: 1.5rem;
            margin-bottom: 2rem;
        }

        .stat-card {
            background: rgba(255, 255, 255, 0.05);
            padding: 1.5rem;
            border-radius: 1rem;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255, 255, 255, 0.1);
            transition: all 0.3s ease;
            position: relative;
            overflow: hidden;
        }

        .stat-card::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            height: 3px;
            background: linear-gradient(90deg, var(--primary-color), var(--info));
            opacity: 0;
            transition: opacity 0.3s ease;
        }

        .stat-card:hover {
            transform: translateY(-4px);
            box-shadow: 0 12px 40px rgba(0, 0, 0, 0.4);
        }

        .stat-card:hover::before {
            opacity: 1;
        }

        .stat-header {
            display: flex;
            align-items: center;
            justify-content: space-between;
            margin-bottom: 1rem;
        }

        .stat-icon {
            font-size: 1.8rem;
        }

        .stat-trend {
            font-size: 0.875rem;
            padding: 0.25rem 0.75rem;
            border-radius: 2rem;
            font-weight: 600;
        }

        .trend-up {
            background: rgba(16, 185, 129, 0.1);
            color: var(--success);
            border: 1px solid rgba(16, 185, 129, 0.2);
        }

        .trend-down {
            background: rgba(239, 68, 68, 0.1);
            color: var(--error);
            border: 1px solid rgba(239, 68, 68, 0.2);
        }

        .stat-value {
            font-size: 2.25rem;
            font-weight: 700;
            color: white;
            margin-bottom: 0.5rem;
            font-variant-numeric: tabular-nums;
        }

        .stat-label {
            font-size: 0.95rem;
            color: var(--text-secondary);
            font-weight: 500;
        }

        /* ===== CHARTS SECTION ===== */
        .charts-section {
            display: grid;
            grid-template-columns: 2fr 1fr;
            gap: 1.5rem;
            margin-bottom: 2rem;
        }

        .chart-card {
            background: rgba(255, 255, 255, 0.05);
            padding: 1.5rem;
            border-radius: 1rem;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255, 255, 255, 0.1);
            min-height: 350px;
        }

        .chart-header {
            display: flex;
            align-items: center;
            justify-content: space-between;
            margin-bottom: 1.5rem;
            padding-bottom: 1rem;
            border-bottom: 1px solid rgba(255, 255, 255, 0.1);
        }

        .chart-title {
            font-size: 1.25rem;
            font-weight: 600;
            color: white;
        }

        .chart-controls {
            display: flex;
            gap: 0.5rem;
        }

        .chart-btn {
            background: transparent;
            border: 1px solid rgba(255, 255, 255, 0.2);
            color: rgba(255, 255, 255, 0.7);
            padding: 0.5rem;
            border-radius: 0.375rem;
            cursor: pointer;
            transition: all 0.2s ease;
            width: 32px;
            height: 32px;
            display: flex;
            align-items: center;
            justify-content: center;
        }

        .chart-btn:hover {
            background: rgba(255, 255, 255, 0.1);
            border-color: rgba(255, 255, 255, 0.3);
            color: white;
        }

        .chart-container {
            height: 250px;
            display: flex;
            align-items: center;
            justify-content: center;
            color: var(--text-secondary);
            font-size: 0.875rem;
        }

        /* ===== PERFORMANCE GRID ===== */
        .performance-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
            gap: 1.5rem;
        }

        /* ===== LIVE FEED ===== */
        .live-feed {
            background: rgba(255, 255, 255, 0.05);
            padding: 1.5rem;
            border-radius: 1rem;
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255, 255, 255, 0.1);
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
        }

        .feed-header {
            display: flex;
            align-items: center;
            justify-content: space-between;
            margin-bottom: 1rem;
            padding-bottom: 1rem;
            border-bottom: 1px solid rgba(255, 255, 255, 0.1);
        }

        .feed-stats {
            display: flex;
            align-items: center;
            gap: 1rem;
        }

        .feed-count {
            font-size: 0.875rem;
            color: var(--text-secondary);
        }

        .clear-feed-btn {
            background: transparent;
            border: 1px solid rgba(255, 255, 255, 0.2);
            color: rgba(255, 255, 255, 0.7);
            padding: 0.375rem 0.75rem;
            border-radius: 0.375rem;
            cursor: pointer;
            transition: all 0.2s ease;
            font-size: 0.875rem;
        }

        .clear-feed-btn:hover {
            background: rgba(239, 68, 68, 0.1);
            color: var(--error);
            border-color: rgba(239, 68, 68, 0.3);
        }

        /* ===== FEED CONTROLS ===== */
        .feed-controls {
            display: flex;
            gap: 0.5rem;
            margin-bottom: 1.5rem;
            flex-wrap: wrap;
        }

        .filter-btn {
            background: transparent;
            border: 1px solid rgba(255, 255, 255, 0.2);
            color: rgba(255, 255, 255, 0.7);
            padding: 0.375rem 1rem;
            border-radius: 2rem;
            font-size: 0.875rem;
            font-weight: 500;
            cursor: pointer;
            transition: all 0.2s ease;
        }

        .filter-btn:hover {
            background: rgba(255, 255, 255, 0.1);
            color: white;
            border-color: rgba(255, 255, 255, 0.3);
            transform: translateY(-1px);
        }

        .filter-btn.active {
            background: var(--primary-color);
            color: white;
            border-color: var(--primary-color);
        }

        /* ===== FEED CONTAINER ===== */
        .feed-container {
            max-height: 400px;
            overflow-y: auto;
            margin: 0 -1.5rem;
            padding: 0 1.5rem;
        }

        .feed-container::-webkit-scrollbar {
            width: 6px;
        }

        .feed-container::-webkit-scrollbar-track {
            background: transparent;
        }

        .feed-container::-webkit-scrollbar-thumb {
            background: rgba(102, 126, 234, 0.5);
            border-radius: 3px;
        }

        .feed-item {
            padding: 1rem 0;
            border-bottom: 1px solid rgba(255, 255, 255, 0.05);
            display: flex;
            align-items: center;
            gap: 1rem;
            transition: all 0.2s ease;
            animation: slideIn 0.3s ease;
        }

        @keyframes slideIn {
            from {
                opacity: 0;
                transform: translateX(-20px);
            }
            to {
                opacity: 1;
                transform: translateX(0);
            }
        }

        .feed-item:hover {
            background: rgba(102, 126, 234, 0.05);
            margin: 0 -1rem;
            padding-left: 1rem;
            padding-right: 1rem;
            border-radius: 0.5rem;
        }

        .feed-icon {
            width: 10px;
            height: 10px;
            border-radius: 50%;
            flex-shrink: 0;
            position: relative;
        }

        .feed-icon.email-sent { background: var(--primary-color); }
        .feed-icon.email-opened { background: var(--success); }
        .feed-icon.email-clicked { background: var(--warning); }
        .feed-icon.loom-clicked { background: var(--info); }

        .feed-content {
            flex: 1;
            font-size: 0.875rem;
            color: rgba(255, 255, 255, 0.9);
        }

        .feed-time {
            font-size: 0.75rem;
            color: var(--text-secondary);
        }

        /* ===== FOOTER ===== */
        .dashboard-footer {
            background: rgba(0, 0, 0, 0.3);
            backdrop-filter: blur(10px);
            border-top: 1px solid rgba(255, 255, 255, 0.1);
            padding: 1.5rem;
            margin-top: 3rem;
        }

        .footer-content {
            max-width: 1400px;
            margin: 0 auto;
            display: flex;
            justify-content: space-between;
            align-items: center;
            color: rgba(255, 255, 255, 0.7);
            font-size: 0.875rem;
        }

        .footer-actions {
            display: flex;
            gap: 0.5rem;
        }

        .footer-btn {
            background: transparent;
            border: 1px solid rgba(255, 255, 255, 0.1);
            color: rgba(255, 255, 255, 0.6);
            padding: 0.375rem 0.75rem;
            border-radius: 0.375rem;
            font-size: 0.75rem;
            cursor: pointer;
            transition: all 0.2s ease;
        }

        .footer-btn:hover {
            background: rgba(255, 255, 255, 0.05);
            color: white;
            border-color: rgba(255, 255, 255, 0.2);
        }

        /* ===== TOAST ===== */
        .toast-container {
            position: fixed;
            top: 1rem;
            right: 1rem;
            z-index: 10000;
            display: flex;
            flex-direction: column;
            gap: 0.5rem;
        }

        .toast {
            background: rgba(30, 41, 59, 0.95);
            border-radius: 0.5rem;
            box-shadow: 0 4px 24px rgba(0, 0, 0, 0.3);
            backdrop-filter: blur(10px);
            min-width: 300px;
            transform: translateX(120%);
            transition: transform 0.3s ease;
            border-left: 4px solid var(--primary-color);
        }

        .toast.show {
            transform: translateX(0);
        }

        .toast.hiding {
            transform: translateX(120%);
        }

        .toast-content {
            padding: 1rem;
            display: flex;
            align-items: center;
            gap: 0.75rem;
            color: white;
        }

        .toast-icon {
            font-size: 1.25rem;
        }

        .toast-success {
            border-left-color: var(--success);
        }

        .toast-error {
            border-left-color: var(--error);
        }

        /* ===== STATUS INDICATOR ===== */
        .status-indicator {
            position: fixed;
            top: 1rem;
            left: 1rem;
            padding: 0.5rem 1rem;
            border-radius: 0.5rem;
            color: white;
            font-weight: 600;
            font-size: 0.875rem;
            backdrop-filter: blur(10px);
            display: flex;
            align-items: center;
            gap: 0.5rem;
            box-shadow: 0 4px 16px rgba(0, 0, 0, 0.3);
        }

        .status-online {
            background: rgba(16, 185, 129, 0.9);
        }

        .status-offline {
            background: rgba(239, 68, 68, 0.9);
        }

        /* ===== RESPONSIVE ===== */
        @media (max-width: 768px) {
            .charts-section {
                grid-template-columns: 1fr;
            }
            
            .stats-grid {
                grid-template-columns: 1fr;
            }
            
            .performance-grid {
                grid-template-columns: 1fr;
            }
            
            .controls-section {
                flex-direction: column;
                gap: 1rem;
            }
            
            .btn-text {
                display: none;
            }
            
            .header-content h1 {
                font-size: 2rem;
            }
        }

        /* ===== UTILITIES ===== */
        .hidden {
            display: none !important;
        }

        .modal-overlay {
            display: none;
        }

        .skip-nav {
            position: absolute;
            top: -40px;
            left: 0;
        }
    </style>
</head>
<body>
    <!-- Loading Screen -->
    <div class="loading-screen hidden" id="loadingScreen">
        <div class="spinner-large"></div>
        <div class="loading-text">Chargement du tableau de bord...</div>
    </div>

    <!-- Toast Container -->
    <div class="toast-container" id="toastContainer"></div>

    <!-- Status Indicator -->
    <div class="status-indicator status-online" id="statusIndicator">
        <span id="statusText">🟢 Connecté</span>
    </div>

    <!-- Skip Navigation -->
    <a href="#main-content" class="skip-nav">Aller au contenu principal</a>

    <!-- Main App -->
    <div class="app-container">
        <!-- Header -->
        <header class="dashboard-header">
            <div class="header-content">
                <h1>📧 Hunter Agency Email Engine</h1>
                <p>Tableau de bord temps réel ultra-performant</p>
            </div>
            
            <nav class="module-nav">
                <button class="module-btn active">📧 Email Engine</button>
                <button class="module-btn" disabled>📱 Social (Bientôt)</button>
                <button class="module-btn" disabled>💰 Revenue (Bientôt)</button>
            </nav>
        </header>

        <!-- Main Content -->
        <main class="main-container" id="main-content">
            <!-- Controls -->
            <section class="controls-section">
                <div class="control-group">
                    <button class="btn active" data-range="24h">📅 24h</button>
                    <button class="btn" data-range="7d">📊 7j</button>
                    <button class="btn" data-range="30d">📈 30j</button>
                </div>
                
                <div class="control-group">
                    <button class="btn" id="refreshBtn">
                        <span class="btn-icon">🔄</span>
                        <span class="btn-text">Actualiser</span>
                    </button>
                    <button class="btn" id="exportBtn">
                        <span class="btn-icon">💾</span>
                        <span class="btn-text">Export CSV</span>
                    </button>
                    <button class="btn" id="exportPdfBtn">
                        <span class="btn-icon">📄</span>
                        <span class="btn-text">Export PDF</span>
                    </button>
                </div>
                
                <div class="control-group">
                    <button class="theme-toggle" id="themeToggle">🌙</button>
                    <select class="language-select">
                        <option value="fr">🇫🇷 Français</option>
                        <option value="en">🇬🇧 English</option>
                    </select>
                </div>
            </section>

            <!-- Stats Grid -->
            <section class="stats-grid" id="statsGrid">
                <div class="stat-card">
                    <div class="stat-header">
                        <span class="stat-icon">📧</span>
                        <span class="stat-trend trend-up">+15%</span>
                    </div>
                    <div class="stat-value">12,543</div>
                    <div class="stat-label">Emails Envoyés</div>
                </div>
                
                <div class="stat-card">
                    <div class="stat-header">
                        <span class="stat-icon">📖</span>
                        <span class="stat-trend trend-up">+5.2%</span>
                    </div>
                    <div class="stat-value">68.4%</div>
                    <div class="stat-label">Taux d'Ouverture</div>
                </div>
                
                <div class="stat-card">
                    <div class="stat-header">
                        <span class="stat-icon">🎯</span>
                        <span class="stat-trend trend-up">+2.1%</span>
                    </div>
                    <div class="stat-value">24.7%</div>
                    <div class="stat-label">Taux de Clic</div>
                </div>
                
                <div class="stat-card">
                    <div class="stat-header">
                        <span class="stat-icon">💬</span>
                        <span class="stat-trend trend-down">-1.4%</span>
                    </div>
                    <div class="stat-value">18.3%</div>
                    <div class="stat-label">Taux de Réponse</div>
                </div>
                
                <div class="stat-card">
                    <div class="stat-header">
                        <span class="stat-icon">🎬</span>
                        <span class="stat-trend trend-up">+48%</span>
                    </div>
                    <div class="stat-value">892</div>
                    <div class="stat-label">Clics Loom</div>
                </div>
                
                <div class="stat-card">
                    <div class="stat-header">
                        <span class="stat-icon">🔄</span>
                        <span class="stat-trend trend-up">+3</span>
                    </div>
                    <div class="stat-value">47</div>
                    <div class="stat-label">Séquences Actives</div>
                </div>
            </section>

            <!-- Charts Section -->
            <section class="charts-section">
                <article class="chart-card">
                    <div class="chart-header">
                        <h2 class="chart-title">📈 Tendances de Performance</h2>
                        <div class="chart-controls">
                            <button class="chart-btn">⛶</button>
                            <button class="chart-btn">⚙️</button>
                        </div>
                    </div>
                    <div class="chart-container">
                        <canvas id="performanceChart"></canvas>
                    </div>
                </article>

                <article class="chart-card">
                    <div class="chart-header">
                        <h2 class="chart-title">🎬 Performance Loom</h2>
                    </div>
                    <div class="chart-container">
                        <canvas id="loomChart"></canvas>
                    </div>
                </article>
            </section>

            <!-- Performance Grid -->
            <section class="performance-grid">
                <article class="chart-card">
                    <div class="chart-header">
                        <h2 class="chart-title">📊 Distribution des Statuts</h2>
                        <button class="chart-btn">👁️ Détails</button>
                    </div>
                    <div class="chart-container">
                        <canvas id="statusChart"></canvas>
                    </div>
                </article>

                <article class="chart-card">
                    <div class="chart-header">
                        <h2 class="chart-title">🕒 Volume par Heure</h2>
                    </div>
                    <div class="chart-container">
                        <canvas id="hourlyChart"></canvas>
                    </div>
                </article>

                <!-- Live Feed -->
                <article class="live-feed">
                    <div class="feed-header">
                        <h2 class="chart-title">🔴 Activité Temps Réel</h2>
                        <div class="feed-stats">
                            <span class="feed-count" id="feedCount">3 événements</span>
                            <button class="clear-feed-btn" id="clearFeedBtn">🗑️</button>
                        </div>
                    </div>
                    
                    <div class="feed-controls">
                        <button class="filter-btn active" data-filter="all">Tout</button>
                        <button class="filter-btn" data-filter="email-sent">📧 Envoyés</button>
                        <button class="filter-btn" data-filter="email-opened">👀 Ouverts</button>
                        <button class="filter-btn" data-filter="email-clicked">🎯 Cliqués</button>
                        <button class="filter-btn" data-filter="loom-clicked">🎬 Loom</button>
                    </div>
                    
                    <div class="feed-container" id="activityFeed">
                        <div class="feed-item" data-type="email-sent">
                            <div class="feed-icon email-sent"></div>
                            <div class="feed-content">Email envoyé à contact@example.com</div>
                            <div class="feed-time">14:32</div>
                        </div>
                        <div class="feed-item" data-type="email-opened">
                            <div class="feed-icon email-opened"></div>
                            <div class="feed-content">Email ouvert par john.doe@company.com</div>
                            <div class="feed-time">14:28</div>
                        </div>
                        <div class="feed-item" data-type="loom-clicked">
                            <div class="feed-icon loom-clicked"></div>
                            <div class="feed-content">Vidéo Loom visionnée par client@business.fr</div>
                            <div class="feed-time">14:15</div>
                        </div>
                    </div>
                </article>
            </section>
        </main>

        <!-- Footer -->
        <footer class="dashboard-footer">
            <div class="footer-content">
                <div class="footer-info">
                    <span>Dernière mise à jour: <time id="lastUpdate">14:32</time></span>
                    <span>Version 3.0.0</span>
                </div>
                <div class="footer-actions">
                    <button class="footer-btn">❓ Aide</button>
                    <button class="footer-btn">💌 Feedback</button>
                </div>
            </div>
        </footer>
    </div>

    <!-- Chart.js avec fallback -->
    <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.min.js"></script>
    
    <script>
        // Attendre que Chart.js soit chargé ou utiliser un placeholder
        window.addEventListener('load', function() {
            if (typeof Chart !== 'undefined') {
                // Configuration des graphiques
                Chart.defaults.color = '#94a3b8';
                Chart.defaults.borderColor = 'rgba(255, 255, 255, 0.1)';
                Chart.defaults.font.family = 'Inter';
                
                // Performance Chart
                const perfCtx = document.getElementById('performanceChart');
                if (perfCtx) {
                    new Chart(perfCtx, {
                type: 'line',
                data: {
                    labels: ['Lun', 'Mar', 'Mer', 'Jeu', 'Ven', 'Sam', 'Dim'],
                    datasets: [{
                        label: 'Emails Envoyés',
                        data: [1250, 1890, 2100, 1950, 2350, 1820, 1600],
                        borderColor: '#667eea',
                        backgroundColor: 'rgba(102, 126, 234, 0.1)',
                        tension: 0.4
                    }, {
                        label: 'Emails Ouverts',
                        data: [850, 1290, 1435, 1330, 1605, 1240, 1090],
                        borderColor: '#10b981',
                        backgroundColor: 'rgba(16, 185, 129, 0.1)',
                        tension: 0.4
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: {
                            display: true,
                            position: 'bottom'
                        }
                    },
                    scales: {
                        y: {
                            grid: {
                                color: 'rgba(255, 255, 255, 0.05)'
                            }
                        },
                        x: {
                            grid: {
                                color: 'rgba(255, 255, 255, 0.05)'
                            }
                        }
                    }
                }
            });
        }
        
        // Loom Chart
        const loomCtx = document.getElementById('loomChart');
        if (loomCtx) {
            new Chart(loomCtx, {
                type: 'bar',
                data: {
                    labels: ['Sans Loom', 'Avec Loom'],
                    datasets: [{
                        label: 'Taux de Clic',
                        data: [18.5, 42.7],
                        backgroundColor: ['rgba(107, 114, 128, 0.8)', 'rgba(59, 130, 246, 0.8)'],
                        borderColor: ['#6b7280', '#3b82f6'],
                        borderWidth: 1
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    scales: {
                        y: {
                            beginAtZero: true,
                            max: 50,
                            grid: {
                                color: 'rgba(255, 255, 255, 0.05)'
                            }
                        },
                        x: {
                            grid: {
                                display: false
                            }
                        }
                    }
                }
            });
        }
        
        // Status Chart
        const statusCtx = document.getElementById('statusChart');
        if (statusCtx) {
            new Chart(statusCtx, {
                type: 'doughnut',
                data: {
                    labels: ['Envoyés', 'Ouverts', 'Cliqués', 'Répondus'],
                    datasets: [{
                        data: [12543, 8572, 3098, 2295],
                        backgroundColor: [
                            'rgba(102, 126, 234, 0.8)',
                            'rgba(16, 185, 129, 0.8)',
                            'rgba(245, 158, 11, 0.8)',
                            'rgba(59, 130, 246, 0.8)'
                        ],
                        borderColor: ['#667eea', '#10b981', '#f59e0b', '#3b82f6'],
                        borderWidth: 1
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: {
                            position: 'bottom'
                        }
                    }
                }
            });
        }
        
        // Hourly Chart
        const hourlyCtx = document.getElementById('hourlyChart');
        if (hourlyCtx) {
            const hours = Array.from({length: 24}, (_, i) => `${i}h`);
            const data = Array.from({length: 24}, () => Math.floor(Math.random() * 200) + 50);
            
            new Chart(hourlyCtx, {
                type: 'bar',
                data: {
                    labels: hours,
                    datasets: [{
                        label: 'Emails',
                        data: data,
                        backgroundColor: 'rgba(102, 126, 234, 0.6)',
                        borderColor: '#667eea',
                        borderWidth: 1
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    scales: {
                        y: {
                            beginAtZero: true,
                            grid: {
                                color: 'rgba(255, 255, 255, 0.05)'
                            }
                        },
                        x: {
                            grid: {
                                display: false
                            }
                        }
                    }
                }
            });
        }
        
        // JavaScript simplifié
        document.addEventListener('DOMContentLoaded', function() {
            // Theme toggle
            const themeToggle = document.getElementById('themeToggle');
            if (themeToggle) {
                themeToggle.addEventListener('click', function() {
                    const html = document.documentElement;
                    const currentTheme = html.getAttribute('data-theme');
                    const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
                    html.setAttribute('data-theme', newTheme);
                    themeToggle.textContent = newTheme === 'dark' ? '🌙' : '☀️';
                    showToast('Thème modifié', 'success');
                });
            }
            
            // Période buttons
            document.querySelectorAll('[data-range]').forEach(btn => {
                btn.addEventListener('click', function(e) {
                    document.querySelectorAll('[data-range]').forEach(b => b.classList.remove('active'));
                    e.currentTarget.classList.add('active');
                    showToast(`Période: ${e.currentTarget.dataset.range}`, 'success');
                });
            });
            
            // Filtres
            document.querySelectorAll('.filter-btn').forEach(btn => {
                btn.addEventListener('click', function(e) {
                    document.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('active'));
                    e.currentTarget.classList.add('active');
                    
                    const filter = e.currentTarget.dataset.filter;
                    document.querySelectorAll('.feed-item').forEach(item => {
                        if (filter === 'all' || item.dataset.type === filter) {
                            item.style.display = 'flex';
                        } else {
                            item.style.display = 'none';
                        }
                    });
                });
            });
            
            // Refresh
            const refreshBtn = document.getElementById('refreshBtn');
            if (refreshBtn) {
                refreshBtn.addEventListener('click', function() {
                    refreshBtn.disabled = true;
                    showToast('Actualisation...', 'info');
                    
                    setTimeout(() => {
                        refreshBtn.disabled = false;
                        showToast('Données actualisées!', 'success');
                        updateTime();
                    }, 1000);
                });
            }
            
            // Clear feed
            const clearBtn = document.getElementById('clearFeedBtn');
            if (clearBtn) {
                clearBtn.addEventListener('click', function() {
                    const feed = document.getElementById('activityFeed');
                    feed.innerHTML = '';
                    document.getElementById('feedCount').textContent = '0 événements';
                    showToast('Feed vidé', 'success');
                });
            }
            
            // Export buttons
            document.getElementById('exportBtn')?.addEventListener('click', () => {
                showToast('Export CSV en cours...', 'success');
            });
            
            document.getElementById('exportPdfBtn')?.addEventListener('click', () => {
                showToast('Export PDF en cours...', 'success');
            });
            
            // Update time
            function updateTime() {
                const now = new Date();
                const timeStr = now.toLocaleTimeString('fr-FR', { hour: '2-digit', minute: '2-digit' });
                document.getElementById('lastUpdate').textContent = timeStr;
            }
            
            // Toast function
            function showToast(message, type = 'info') {
                const container = document.getElementById('toastContainer');
                const toast = document.createElement('div');
                toast.className = `toast toast-${type} show`;
                
                const icons = {
                    success: '✅',
                    error: '❌',
                    warning: '⚠️',
                    info: 'ℹ️'
                };
                
                toast.innerHTML = `
                    <div class="toast-content">
                        <span class="toast-icon">${icons[type]}</span>
                        <span class="toast-message">${message}</span>
                    </div>
                `;
                
                container.appendChild(toast);
                
                setTimeout(() => {
                    toast.classList.add('hiding');
                    setTimeout(() => toast.remove(), 300);
                }, 3000);
            }
            
            // Initial time update
            updateTime();
        });
    </script>
</body>
</html>
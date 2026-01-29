import React, { useState, useEffect } from 'react';
import { CheckCircle2, Circle, ChevronDown, ChevronRight, FileText, BarChart3, Target, Presentation, Database, Save, RefreshCw, Zap, TrendingUp } from 'lucide-react';

// ==============================================================================
// WBB 2026 SCOUT REPORTS - PROJECT TRACKER
// Automated weekly scouting reports demonstrating repeatable analytics systems
// ==============================================================================

const PROJECT_NAME = "WBB 2026 Scout Reports";
const STORAGE_KEY = 'wbb-2026-scout-reports-tracker';

const ProjectTracker = () => {
  const [expandedSections, setExpandedSections] = useState({
    phase1: true,
    phase2: true,
    phase3: true,
    phase4: true
  });

  const [tasks, setTasks] = useState({
    // PHASE 1: Foundation (Week 1-2) - 12 hrs
    'setup-repo-structure': false,
    'install-dependencies': false,
    'test-api-access': false,
    'build-incremental-pull': false,
    'create-tracking-parquet': false,
    'define-canonical-tables': false,
    'implement-possessions': false,
    'implement-ortg-drtg': false,
    'implement-efg-ts': false,
    'implement-tov-pct': false,
    'implement-reb-pct': false,
    'implement-ast-ftr': false,
    'build-d1-benchmarks': false,
    'compute-percentiles': false,
    'create-percentile-tiers': false,
    'create-role-labels': false,
    'create-game-context': false,

    // PHASE 2: Tableau Build (Week 3-4) - 15 hrs
    'tableau-game-summary': false,
    'tableau-metrics-breakdown': false,
    'tableau-player-impact': false,
    'tableau-game-selector': false,
    'tableau-team-toggle': false,
    'tableau-metric-toggles': false,
    'design-neutral-palette': false,
    'design-percentile-encoding': false,
    'design-visual-hierarchy': false,
    'design-mobile-friendly': false,
    'annotation-why-won': false,
    'annotation-key-stats': false,
    'annotation-benchmarks': false,
    'annotation-tooltips': false,

    // PHASE 3: Automation (Week 5) - 6 hrs
    'script-weekly-pull': false,
    'script-skip-processed': false,
    'script-compute-metrics': false,
    'script-update-benchmarks': false,
    'script-export-tableau': false,
    'github-action-schedule': false,
    'github-action-manual': false,
    'github-action-workflow': false,
    'docs-readme': false,
    'docs-data-dictionary': false,
    'docs-methodology': false,
    'docs-examples': false,

    // PHASE 4: Portfolio Integration (Week 6) - 4 hrs
    'publish-tableau-public': false,
    'write-case-study': false,
    'create-github-readme': false,
    'add-screenshots': false,
    'link-future-projects': false
  });

  const [saveStatus, setSaveStatus] = useState('');
  const [isLoading, setIsLoading] = useState(true);

  // Load saved state on mount
  useEffect(() => {
    const loadSavedState = async () => {
      try {
        const result = await window.storage.get(STORAGE_KEY);
        if (result && result.value) {
          const savedData = JSON.parse(result.value);
          if (savedData.tasks) {
            setTasks(prev => ({ ...prev, ...savedData.tasks }));
          }
          if (savedData.expandedSections) {
            setExpandedSections(prev => ({ ...prev, ...savedData.expandedSections }));
          }
          setSaveStatus('✓ Loaded saved progress');
        } else {
          setSaveStatus('Starting fresh');
        }
      } catch (error) {
        console.log('No saved state found, using defaults');
        setSaveStatus('Starting fresh');
      }
      setIsLoading(false);
    };

    loadSavedState();
  }, []);

  // Auto-save when tasks change
  useEffect(() => {
    if (isLoading) return;

    const saveState = async () => {
      try {
        const dataToSave = JSON.stringify({
          tasks,
          expandedSections,
          lastUpdated: new Date().toISOString()
        });
        await window.storage.set(STORAGE_KEY, dataToSave);
        setSaveStatus('✓ Saved');
        setTimeout(() => setSaveStatus(''), 2000);
      } catch (error) {
        console.error('Failed to save:', error);
        setSaveStatus('⚠ Save failed');
      }
    };

    saveState();
  }, [tasks, isLoading]);

  const toggleSection = (section) => {
    setExpandedSections(prev => ({
      ...prev,
      [section]: !prev[section]
    }));
  };

  const toggleTask = (taskId) => {
    setTasks(prev => ({
      ...prev,
      [taskId]: !prev[taskId]
    }));
  };

  const getPhaseProgress = (taskIds) => {
    const completed = taskIds.filter(id => tasks[id]).length;
    return { completed, total: taskIds.length, percent: Math.round((completed / taskIds.length) * 100) };
  };

  const resetProgress = async () => {
    if (confirm('Are you sure you want to reset all progress? This cannot be undone.')) {
      try {
        await window.storage.delete(STORAGE_KEY);
        window.location.reload();
      } catch (error) {
        console.error('Failed to reset:', error);
      }
    }
  };

  const TaskItem = ({ id, label, requirement, dataFile, notes, priority, hours }) => (
    <div
      className={`flex items-start gap-3 p-3 rounded-lg cursor-pointer transition-all ${
        tasks[id] ? 'bg-green-50 border border-green-200' : 'bg-white border border-gray-200 hover:border-indigo-300'
      }`}
      onClick={() => toggleTask(id)}
    >
      {tasks[id] ? (
        <CheckCircle2 className="w-5 h-5 text-green-600 mt-0.5 flex-shrink-0" />
      ) : (
        <Circle className="w-5 h-5 text-gray-400 mt-0.5 flex-shrink-0" />
      )}
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2 flex-wrap">
          <span className={`font-medium ${tasks[id] ? 'text-green-900 line-through' : 'text-gray-900'}`}>
            {label}
          </span>
          {priority && (
            <span className="px-2 py-0.5 text-xs font-medium bg-orange-100 text-orange-700 rounded">
              {priority}
            </span>
          )}
          {hours && (
            <span className="px-2 py-0.5 text-xs font-medium bg-blue-100 text-blue-700 rounded">
              {hours}
            </span>
          )}
        </div>
        {requirement && (
          <p className="text-sm text-gray-600 mt-1">{requirement}</p>
        )}
        {dataFile && (
          <p className="text-xs text-indigo-600 mt-1 font-mono">{dataFile}</p>
        )}
        {notes && (
          <p className="text-xs text-gray-500 mt-1 italic">{notes}</p>
        )}
      </div>
    </div>
  );

  const phases = [
    {
      id: 'phase1',
      title: 'Phase 1: Foundation (Week 1-2)',
      icon: Database,
      color: 'blue',
      hours: '12 hrs',
      tasks: [
        // Data Pipeline Setup
        {
          id: 'setup-repo-structure',
          label: 'Set Up Repository Structure',
          requirement: 'Create wbb_2026_scout_reports/ with all subdirectories',
          notes: 'data/, scripts/, notebooks/, docs/, tableau/',
          priority: 'HIGH'
        },
        {
          id: 'install-dependencies',
          label: 'Install sportsdataverse + Dependencies',
          requirement: 'Set up Python environment with wehoop package',
          notes: 'pandas, numpy, sportsdataverse, pyarrow'
        },
        {
          id: 'test-api-access',
          label: 'Test API Access with 2025 Game',
          requirement: 'Pull one test game from sportsdataverse to verify access',
          dataFile: 'data/raw/test_game.parquet'
        },
        {
          id: 'build-incremental-pull',
          label: 'Build Incremental Pull Script',
          requirement: 'Create script to skip existing games and pull new data',
          dataFile: 'scripts/weekly_pull.py',
          priority: 'HIGH'
        },
        {
          id: 'create-tracking-parquet',
          label: 'Create Tracking Parquet',
          requirement: 'Track which games have been processed',
          dataFile: 'data/tracking/processed_games.parquet'
        },

        // Schema & Metrics Layer
        {
          id: 'define-canonical-tables',
          label: 'Define Canonical Tables',
          requirement: 'Create game_summary and player_game table schemas',
          dataFile: 'docs/data_dictionary.md',
          priority: 'HIGH'
        },
        {
          id: 'implement-possessions',
          label: 'Implement Possessions Formula',
          requirement: 'FGA + 0.44*FTA - ORB + TOV',
          dataFile: 'scripts/metrics.py',
          notes: 'Foundation for efficiency metrics'
        },
        {
          id: 'implement-ortg-drtg',
          label: 'Implement ORtg/DRtg',
          requirement: '100 * PTS / Poss',
          dataFile: 'scripts/metrics.py'
        },
        {
          id: 'implement-efg-ts',
          label: 'Implement eFG% and TS%',
          requirement: 'eFG = (FGM + 0.5*3PM) / FGA, TS = PTS / (2 * (FGA + 0.44*FTA))',
          dataFile: 'scripts/metrics.py'
        },
        {
          id: 'implement-tov-pct',
          label: 'Implement TOV%',
          requirement: 'TOV / Poss',
          dataFile: 'scripts/metrics.py'
        },
        {
          id: 'implement-reb-pct',
          label: 'Implement OREB%/DREB%',
          requirement: 'ORB / (ORB + OppDRB)',
          dataFile: 'scripts/metrics.py'
        },
        {
          id: 'implement-ast-ftr',
          label: 'Implement AST% and FTr',
          requirement: 'AST / FGM, FTA / FGA',
          dataFile: 'scripts/metrics.py'
        },
        {
          id: 'build-d1-benchmarks',
          label: 'Build D1 Benchmark Table',
          requirement: 'Aggregate season data for percentile calculations',
          dataFile: 'data/benchmarks/d1_benchmarks_2025.csv',
          priority: 'HIGH'
        },
        {
          id: 'compute-percentiles',
          label: 'Compute Percentiles',
          requirement: 'Calculate national and weekly percentile ranks',
          dataFile: 'scripts/benchmarks.py'
        },

        // Categorical Labels
        {
          id: 'create-percentile-tiers',
          label: 'Create Percentile Tier Labels',
          requirement: 'Elite (≥90), Great (75-89), Above Avg (60-74), etc.',
          dataFile: 'scripts/labels.py',
          notes: '6 tiers for categorical encoding'
        },
        {
          id: 'create-role-labels',
          label: 'Create Player Role Labels',
          requirement: 'High Usage/Efficient, Efficient Role Player, etc.',
          dataFile: 'scripts/labels.py',
          notes: 'Based on USG% and TS% combinations'
        },
        {
          id: 'create-game-context',
          label: 'Create Game Outcome Context',
          requirement: 'Close Game, Blowout, Upset, Ranked Matchup tags',
          dataFile: 'scripts/labels.py'
        }
      ]
    },
    {
      id: 'phase2',
      title: 'Phase 2: Tableau Build (Week 3-4)',
      icon: BarChart3,
      color: 'purple',
      hours: '15 hrs',
      tasks: [
        // Dashboard Structure
        {
          id: 'tableau-game-summary',
          label: 'Game Summary View',
          requirement: 'Build team comparison table with Four Factors',
          notes: 'Include "Why They Won" callout box',
          priority: 'HIGH'
        },
        {
          id: 'tableau-metrics-breakdown',
          label: 'Metrics Breakdown View',
          requirement: 'Shooting efficiency, ball control, rebounding sections',
          notes: 'Horizontal bar charts with percentile encoding',
          priority: 'HIGH'
        },
        {
          id: 'tableau-player-impact',
          label: 'Player Impact View',
          requirement: 'Top performers table + efficiency vs volume scatterplot',
          notes: 'Role labels and categorical markers',
          priority: 'HIGH'
        },
        {
          id: 'tableau-game-selector',
          label: 'Game Selector Filter',
          requirement: 'Dropdown to select which game to analyze',
          notes: 'Show game date, teams, score in selector'
        },
        {
          id: 'tableau-team-toggle',
          label: 'Team Toggle Filter',
          requirement: 'Switch between Team A/Team B perspective',
          notes: 'Dynamic reference lines and colors'
        },
        {
          id: 'tableau-metric-toggles',
          label: 'Metric Toggle Filters',
          requirement: 'Show/hide specific metric categories',
          notes: 'Optional: filter by percentile threshold'
        },

        // Design Standards
        {
          id: 'design-neutral-palette',
          label: 'Neutral Palette with Semantic Highlights',
          requirement: 'Gray base, green for positive, red for negative',
          notes: 'Avoid team colors in data encoding'
        },
        {
          id: 'design-percentile-encoding',
          label: 'Percentile Color Encoding',
          requirement: '0-100 diverging scale (red → gray → green)',
          notes: 'Consistent across all percentile fields'
        },
        {
          id: 'design-visual-hierarchy',
          label: 'Clear Visual Hierarchy',
          requirement: 'Title > Section > Chart > Annotation',
          notes: 'Font sizes: 24pt → 18pt → 12pt → 10pt'
        },
        {
          id: 'design-mobile-friendly',
          label: 'Mobile-Friendly Layout',
          requirement: 'Test on phone viewport, ensure readability',
          notes: 'Consider vertical stacking for small screens'
        },

        // Annotations & Storytelling
        {
          id: 'annotation-why-won',
          label: '"Why They Won" Callout Box',
          requirement: 'Auto-generated from top 3 metric differentials',
          notes: 'Rules: OREB% > TOV% > eFG% > FTr priority',
          priority: 'HIGH'
        },
        {
          id: 'annotation-key-stats',
          label: 'Key Stat Highlights',
          requirement: 'Pull out standout performances (e.g., "42% OREB - Elite")',
          notes: 'Use conditional formatting for emphasis'
        },
        {
          id: 'annotation-benchmarks',
          label: 'Benchmark Reference Lines',
          requirement: 'Show D1 average on charts where relevant',
          notes: 'Dotted gray line with label'
        },
        {
          id: 'annotation-tooltips',
          label: 'Tooltip Explanations',
          requirement: 'Define metrics for non-technical viewers',
          notes: 'Example: "eFG% weights 3-pointers appropriately"'
        }
      ]
    },
    {
      id: 'phase3',
      title: 'Phase 3: Automation (Week 5)',
      icon: Zap,
      color: 'green',
      hours: '6 hrs',
      tasks: [
        // Weekly Pull Script
        {
          id: 'script-weekly-pull',
          label: 'Weekly Pull Script',
          requirement: 'python scripts/weekly_pull.py --week 2025-01-06',
          dataFile: 'scripts/weekly_pull.py',
          priority: 'HIGH'
        },
        {
          id: 'script-skip-processed',
          label: 'Skip Already-Processed Games',
          requirement: 'Check processed_games.parquet, skip existing game_ids',
          notes: 'Prevent duplicate processing'
        },
        {
          id: 'script-compute-metrics',
          label: 'Compute Derived Metrics',
          requirement: 'Call metrics.py functions for new games',
          notes: 'All Four Factors + efficiency metrics'
        },
        {
          id: 'script-update-benchmarks',
          label: 'Update Benchmark Tables',
          requirement: 'Recalculate D1 percentiles with new data',
          dataFile: 'data/benchmarks/d1_benchmarks_2025.csv'
        },
        {
          id: 'script-export-tableau',
          label: 'Export Tableau-Ready Dataset',
          requirement: 'Generate final CSV for Tableau consumption',
          dataFile: 'data/processed/tableau_export.csv',
          priority: 'HIGH'
        },

        // GitHub Action Workflow
        {
          id: 'github-action-schedule',
          label: 'GitHub Action Schedule',
          requirement: 'Cron: Every Monday at 6 AM EST',
          dataFile: '.github/workflows/weekly_pull.yml',
          notes: 'cron: "0 11 * * 1" (6 AM EST = 11 AM UTC)'
        },
        {
          id: 'github-action-manual',
          label: 'Manual Dispatch Option',
          requirement: 'workflow_dispatch trigger for on-demand runs',
          notes: 'Useful for testing and one-off pulls'
        },
        {
          id: 'github-action-workflow',
          label: 'Complete Workflow Steps',
          requirement: '1. Install deps 2. Run weekly_pull.py 3. Commit files',
          notes: 'Add optional webhook notification'
        },

        // Documentation
        {
          id: 'docs-readme',
          label: 'README with Setup Instructions',
          requirement: 'Installation, usage, project overview',
          dataFile: 'README.md',
          priority: 'HIGH'
        },
        {
          id: 'docs-data-dictionary',
          label: 'Data Dictionary',
          requirement: 'Field definitions + sources for all tables',
          dataFile: 'docs/data_dictionary.md',
          priority: 'HIGH'
        },
        {
          id: 'docs-methodology',
          label: 'Methodology Notes',
          requirement: 'Formula references, calculation explanations',
          dataFile: 'docs/methodology.md'
        },
        {
          id: 'docs-examples',
          label: 'Example Outputs',
          requirement: 'Screenshots or sample CSVs',
          dataFile: 'docs/examples/'
        }
      ]
    },
    {
      id: 'phase4',
      title: 'Phase 4: Portfolio Integration (Week 6)',
      icon: Target,
      color: 'red',
      hours: '4 hrs',
      tasks: [
        {
          id: 'publish-tableau-public',
          label: 'Publish to Tableau Public',
          requirement: 'Upload dashboard with public sharing enabled',
          notes: 'Test all filters and interactions live',
          priority: 'HIGH'
        },
        {
          id: 'write-case-study',
          label: 'Write Portfolio Case Study',
          requirement: 'Problem → Approach → Results format',
          dataFile: 'docs/portfolio_writeup.md',
          notes: '1-page summary for portfolio website',
          priority: 'HIGH'
        },
        {
          id: 'create-github-readme',
          label: 'Create GitHub README',
          requirement: 'Project overview, key findings, technical skills',
          notes: 'Include badges for Python, Tableau, automation',
          priority: 'HIGH'
        },
        {
          id: 'add-screenshots',
          label: 'Add Screenshots',
          requirement: 'Dashboard views and example outputs',
          dataFile: 'tableau/exports/',
          notes: 'High-res PNGs for visual appeal'
        },
        {
          id: 'link-future-projects',
          label: 'Link to Future Team Analysis Project',
          requirement: 'Note integration path with team-focused project',
          notes: 'Shared benchmarks, metrics module, combined data source'
        }
      ]
    }
  ];

  const overallProgress = getPhaseProgress(Object.keys(tasks));

  return (
    <div className="min-h-screen bg-gradient-to-br from-indigo-50 to-gray-100 p-6">
      <div className="max-w-6xl mx-auto">
        {/* Header */}
        <div className="bg-white rounded-xl shadow-lg p-6 mb-6">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h1 className="text-3xl font-bold text-gray-900">{PROJECT_NAME}</h1>
              <p className="text-gray-600 mt-1">Automated Weekly Women's Basketball Scouting Reports</p>
              <p className="text-sm text-indigo-600 mt-1">Timeline: 6 weeks • 37 hours total</p>
            </div>
            <div className="flex items-center gap-4">
              <div className="text-right">
                <div className="text-sm text-gray-600">Overall Progress</div>
                <div className="text-2xl font-bold text-indigo-600">
                  {overallProgress.percent}%
                </div>
                <div className="text-xs text-gray-500">
                  {overallProgress.completed}/{overallProgress.total} tasks
                </div>
              </div>
              <button
                onClick={resetProgress}
                className="p-2 text-gray-600 hover:text-red-600 hover:bg-red-50 rounded-lg transition-colors"
                title="Reset all progress"
              >
                <RefreshCw className="w-5 h-5" />
              </button>
            </div>
          </div>

          {/* Progress Bar */}
          <div className="w-full bg-gray-200 rounded-full h-3">
            <div
              className="bg-gradient-to-r from-indigo-500 to-indigo-600 h-3 rounded-full transition-all duration-500"
              style={{ width: `${overallProgress.percent}%` }}
            />
          </div>

          {/* Key Deliverables */}
          <div className="mt-4 grid grid-cols-4 gap-3">
            <div className="bg-blue-50 p-3 rounded-lg">
              <div className="text-xs text-blue-600 font-semibold">DATA PIPELINE</div>
              <div className="text-sm text-gray-700 mt-1">Incremental pulls + benchmarks</div>
            </div>
            <div className="bg-purple-50 p-3 rounded-lg">
              <div className="text-xs text-purple-600 font-semibold">TABLEAU DASHBOARD</div>
              <div className="text-sm text-gray-700 mt-1">3-view condensed reports</div>
            </div>
            <div className="bg-green-50 p-3 rounded-lg">
              <div className="text-xs text-green-600 font-semibold">AUTOMATION</div>
              <div className="text-sm text-gray-700 mt-1">GitHub Action weekly runs</div>
            </div>
            <div className="bg-red-50 p-3 rounded-lg">
              <div className="text-xs text-red-600 font-semibold">PORTFOLIO</div>
              <div className="text-sm text-gray-700 mt-1">Case study + screenshots</div>
            </div>
          </div>

          {/* Save Status */}
          {saveStatus && (
            <div className="mt-3 text-sm text-gray-600 flex items-center gap-2">
              <Save className="w-4 h-4" />
              {saveStatus}
            </div>
          )}
        </div>

        {/* Phase Cards */}
        <div className="space-y-4">
          {phases.map(phase => {
            const progress = getPhaseProgress(phase.tasks.map(t => t.id));
            const Icon = phase.icon;

            return (
              <div key={phase.id} className="bg-white rounded-xl shadow-lg overflow-hidden">
                {/* Phase Header */}
                <div
                  className={`bg-gradient-to-r from-${phase.color}-500 to-${phase.color}-600 text-white p-4 cursor-pointer`}
                  onClick={() => toggleSection(phase.id)}
                >
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-3">
                      {expandedSections[phase.id] ? (
                        <ChevronDown className="w-5 h-5" />
                      ) : (
                        <ChevronRight className="w-5 h-5" />
                      )}
                      <Icon className="w-6 h-6" />
                      <div>
                        <h2 className="text-xl font-bold">{phase.title}</h2>
                        <div className="text-sm opacity-90">{phase.hours}</div>
                      </div>
                    </div>
                    <div className="flex items-center gap-4">
                      <span className="text-sm opacity-90">
                        {progress.completed}/{progress.total} complete
                      </span>
                      <div className="w-24 bg-white/20 rounded-full h-2">
                        <div
                          className="bg-white h-2 rounded-full transition-all duration-500"
                          style={{ width: `${progress.percent}%` }}
                        />
                      </div>
                    </div>
                  </div>
                </div>

                {/* Phase Tasks */}
                {expandedSections[phase.id] && (
                  <div className="p-4 space-y-2">
                    {phase.tasks.map(task => (
                      <TaskItem key={task.id} {...task} />
                    ))}
                  </div>
                )}
              </div>
            );
          })}
        </div>

        {/* Footer Notes */}
        <div className="mt-6 bg-white rounded-xl shadow-lg p-6">
          <h3 className="font-bold text-gray-900 mb-3">Success Criteria</h3>
          <div className="grid grid-cols-2 gap-4 text-sm">
            <div>
              <div className="font-semibold text-gray-700 mb-2">Technical:</div>
              <ul className="space-y-1 text-gray-600">
                <li>• Pipeline runs without manual intervention</li>
                <li>• Metrics match manual calculations (spot-check 5 games)</li>
                <li>• Percentiles align ±2 percentile points</li>
                <li>• GitHub Action completes in &lt;5 minutes</li>
              </ul>
            </div>
            <div>
              <div className="font-semibold text-gray-700 mb-2">Portfolio Value:</div>
              <ul className="space-y-1 text-gray-600">
                <li>• Non-technical viewer understands "why won" in &lt;30s</li>
                <li>• Demonstrates calculated fields (not raw stats)</li>
                <li>• Shows benchmark context for every key metric</li>
                <li>• Code is documented and reproducible</li>
              </ul>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ProjectTracker;

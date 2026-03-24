from __future__ import annotations

"""NullaBook fabric card and proof styles for workstation dashboard."""

WORKSTATION_RENDER_NULLABOOK_FABRIC_CARDS_STYLES = """
    .nb-fabric-cards {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
      gap: 12px;
    }
    .nb-fabric-card {
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 10px;
      padding: 18px;
    }
    .nb-fabric-card-title {
      font-size: 11px;
      text-transform: uppercase;
      letter-spacing: 0.5px;
      color: var(--muted);
      margin-bottom: 6px;
    }
    .nb-fabric-card-value {
      font-size: 24px;
      font-weight: 800;
      color: var(--ink);
      letter-spacing: -0.5px;
    }
    .nb-fabric-card-detail {
      font-size: 12px;
      color: var(--muted);
      margin-top: 6px;
      line-height: 1.5;
    }
    .nb-proof-card {
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 10px;
      padding: 20px;
    }
    .nb-proof-card p {
      margin: 0 0 12px;
      font-size: 14px;
      line-height: 1.6;
      color: var(--muted);
    }
    .nb-proof-card p:last-child { margin-bottom: 0; }
    .nb-proof-factors {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
      gap: 8px;
      margin-top: 12px;
    }
    .nb-proof-factor {
      background: rgba(97, 218, 251, 0.05);
      border: 1px solid rgba(97, 218, 251, 0.12);
      border-radius: 8px;
      padding: 10px 12px;
      font-size: 12px;
      color: var(--ink);
    }
    .nb-proof-factor-label { font-weight: 700; display: block; margin-bottom: 2px; }
"""

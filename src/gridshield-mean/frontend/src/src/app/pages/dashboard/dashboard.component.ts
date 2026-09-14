import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterLink } from '@angular/router';
import { GridshieldService } from '../../services/gridshield.service';
import { Asset, Stats } from '../../models/asset.model';
import { CauseLabelPipe } from '../../pipes/cause-label.pipe';

@Component({
  selector: 'app-dashboard',
  standalone: true,
  imports: [CommonModule, RouterLink, CauseLabelPipe],
  template: `
    <div style="padding:28px 32px 48px;max-width:1200px">
      <div class="hero">
        <h2>&#9889; GridShield</h2>
        <p>Civil-Engineering-Aware Power Grid Advisor &nbsp;|&nbsp; IBM Bob AI Hackathon 2026 &nbsp;|&nbsp; Problem U1: Power Outage Prediction &amp; Grid Equipment Failure Advisor</p>
      </div>

      <div *ngIf="loading" style="text-align:center;padding:40px"><span class="spinner"></span></div>
      <div *ngIf="error" style="color:var(--critical);padding:12px">{{ error }}</div>

      <div *ngIf="!loading && stats" class="kpi-row">
        <div class="kpi red"><div class="val">{{ stats.critical }}</div><div class="lbl">Critical assets</div></div>
        <div class="kpi orange"><div class="val">{{ stats.elevated }}</div><div class="lbl">Elevated assets</div></div>
        <div class="kpi blue"><div class="val">{{ stats.immediate }}</div><div class="lbl">Immediate actions</div></div>
        <div class="kpi green"><div class="val">{{ stats.total }}</div><div class="lbl">Total assets monitored</div></div>
        <div class="kpi blue"><div class="val">{{ (stats.totalCustomers / 1000).toFixed(1) }}k</div><div class="lbl">Customers protected</div></div>
      </div>

      <div *ngIf="!loading && assets.length">
        <p class="page-caption">Top 10 assets by priority score — click any row for full detail.</p>
        <div class="table-wrap">
          <table>
            <thead>
              <tr>
                <th>Asset</th><th>Type</th><th>Band</th>
                <th>Risk</th><th>Priority</th><th>Dominant Cause</th>
                <th>Critical Load</th><th>Customers</th><th>Tier</th>
              </tr>
            </thead>
            <tbody>
              <tr *ngFor="let a of assets.slice(0,10)"
                  [class]="'tint-' + a.risk_band" style="cursor:pointer"
                  [routerLink]="['/asset', a.asset_id]">
                <td><strong>{{ a.asset_id }}</strong></td>
                <td>{{ a.asset_type }}</td>
                <td><span [class]="'badge badge-' + a.risk_band">{{ a.risk_band.toUpperCase() }}</span></td>
                <td>{{ a.risk_score | number:'1.1-1' }}</td>
                <td>{{ a.priority_score | number:'1.4-4' }}</td>
                <td>{{ a.dominant_cause | causeLabel }}</td>
                <td>{{ a.critical_loads }}</td>
                <td>{{ a.downstream_customers | number }}</td>
                <td><span [class]="'tier-badge tier-' + a.action_tier">{{ a.action_tier }}</span></td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <footer style="border-top:1px solid var(--border);padding:16px 0;text-align:center;font-size:0.75rem;color:var(--muted);margin-top:32px">Made with IBM Bob</footer>
    </div>
  `,
})
export class DashboardComponent implements OnInit {
  assets: Asset[] = [];
  stats: Stats | null = null;
  loading = true;
  error = '';

  constructor(private svc: GridshieldService) {}

  ngOnInit() {
    this.svc.getAssets().subscribe({
      next: (a) => { this.assets = a; this.loading = false; },
      error: (e) => { this.error = e.message; this.loading = false; },
    });
    this.svc.getStats().subscribe({ next: (s) => (this.stats = s) });
  }
}

import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { GridshieldService } from '../../services/gridshield.service';
import { Asset, Incident } from '../../models/asset.model';
import { CauseLabelPipe } from '../../pipes/cause-label.pipe';

@Component({
  selector: 'app-reactive',
  standalone: true,
  imports: [CommonModule, CauseLabelPipe],
  template: `
    <div style="padding:28px 32px 48px;max-width:1200px">
      <div class="page-title">&#128201; Reactive vs Preventive Comparison</div>
      <div class="page-caption">Comparing historically incident-prone assets against the current top-10 priority queue — GridShield prevents failures before they happen.</div>

      <div *ngIf="loading" style="text-align:center;padding:40px"><span class="spinner"></span></div>
      <div *ngIf="error" style="color:var(--critical)">{{ error }}</div>

      <ng-container *ngIf="!loading && assets.length">
        <!-- Stat cards -->
        <div class="stat-cards">
          <div class="stat-card"><div class="sv">{{ inBoth }}</div><div class="sl">Top-10 assets also with past incidents</div></div>
          <div class="stat-card"><div class="sv">{{ onlyPriority }}</div><div class="sl">Top-10 assets with NO incident history</div></div>
          <div class="stat-card"><div class="sv">{{ onlyIncident }}</div><div class="sl">Incident assets NOT in top-10</div></div>
        </div>

        <!-- Compare cols -->
        <div class="compare-cols">
          <div class="compare-box reactive">
            <h3>&#128308; Reactive Approach (Historical)</h3>
            <p>&#x2022; {{ totalIncidents }} recorded incidents</p>
            <p>&#x2022; {{ totalDowntime | number:'1.0-0' }} total downtime hours</p>
            <p>&#x2022; Estimated cost of failures: <strong>{{ reactiveCost | currency:'USD':'symbol':'1.0-0' }}</strong></p>
          </div>
          <div class="compare-box preventive">
            <h3>&#128994; GridShield Preventive Queue (Top 10)</h3>
            <p>&#x2022; {{ top10.length }} assets addressed proactively</p>
            <p>&#x2022; {{ top10Customers | number }} customers protected</p>
            <p>&#x2022; Estimated total intervention cost: <strong>{{ top10Cost | currency:'USD':'symbol':'1.0-0' }}</strong></p>
          </div>
        </div>

        <!-- Key takeaway -->
        <div class="info-box">
          <strong>Key takeaway:</strong> GridShield's priority queue places historically incident-prone assets
          ({{ inBoth }} of {{ top10.length }}) in the top-10 <em>before</em> a failure occurs, while intervention costs
          ({{ top10Cost | currency:'USD':'symbol':'1.0-0' }}) are a fraction of reactive costs
          ({{ reactiveCost | currency:'USD':'symbol':'1.0-0' }}).
        </div>

        <!-- Cross-reference table -->
        <p class="page-caption">Top-10 priority assets with incident history cross-reference:</p>
        <div class="table-wrap">
          <table>
            <thead>
              <tr>
                <th>Asset</th><th>Band</th><th>Risk</th><th>Priority</th>
                <th>Cause</th><th>Critical Load</th><th>Customers</th>
                <th>Past Incident?</th><th>Intervention Cost</th>
              </tr>
            </thead>
            <tbody>
              <tr *ngFor="let a of top10" [class]="'tint-' + a.risk_band">
                <td><strong>{{ a.asset_id }}</strong></td>
                <td><span [class]="'badge badge-' + a.risk_band">{{ a.risk_band.toUpperCase() }}</span></td>
                <td>{{ a.risk_score | number:'1.1-1' }}</td>
                <td>{{ a.priority_score | number:'1.4-4' }}</td>
                <td>{{ a.dominant_cause | causeLabel }}</td>
                <td>{{ a.critical_loads }}</td>
                <td>{{ a.downstream_customers | number }}</td>
                <td>
                  <span *ngIf="incidentAssets.has(a.asset_id)" style="color:var(--critical);font-weight:700">Yes</span>
                  <span *ngIf="!incidentAssets.has(a.asset_id)" style="color:var(--normal)">No</span>
                </td>
                <td>{{ a.estimated_intervention_cost | currency:'USD':'symbol':'1.0-0' }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </ng-container>

      <footer style="border-top:1px solid var(--border);padding:16px 0;text-align:center;font-size:0.75rem;color:var(--muted);margin-top:32px">Made with IBM Bob</footer>
    </div>
  `,
})
export class ReactiveComponent implements OnInit {
  assets: Asset[] = [];
  incidents: Incident[] = [];
  loading = true;
  error = '';

  top10: Asset[] = [];
  incidentAssets = new Set<string>();
  inBoth = 0;
  onlyPriority = 0;
  onlyIncident = 0;
  totalIncidents = 0;
  totalDowntime = 0;
  top10Cost = 0;
  top10Customers = 0;
  reactiveCost = 0;

  constructor(private svc: GridshieldService) {}

  ngOnInit() {
    Promise.all([
      this.svc.getAssets().toPromise(),
      this.svc.getIncidents().toPromise(),
    ]).then(([assets, incidents]) => {
      this.assets    = assets!;
      this.incidents = incidents!;
      this.compute();
      this.loading = false;
    }).catch((e) => { this.error = e.message; this.loading = false; });
  }

  compute() {
    this.top10 = this.assets.slice(0, 10);
    this.incidentAssets = new Set(this.incidents.map(i => i.asset_id));
    const top10Ids = new Set(this.top10.map(a => a.asset_id));
    this.inBoth       = [...this.incidentAssets].filter(id => top10Ids.has(id)).length;
    this.onlyPriority = this.top10.filter(a => !this.incidentAssets.has(a.asset_id)).length;
    this.onlyIncident = [...this.incidentAssets].filter(id => !top10Ids.has(id)).length;
    this.totalIncidents = this.incidents.length;
    this.totalDowntime  = this.incidents.reduce((s, i) => s + i.downtime_hours, 0);
    this.top10Cost      = this.top10.reduce((s, a) => s + a.estimated_intervention_cost, 0);
    this.top10Customers = this.top10.reduce((s, a) => s + a.downstream_customers, 0);
    this.reactiveCost   = this.totalDowntime * 50;
  }
}

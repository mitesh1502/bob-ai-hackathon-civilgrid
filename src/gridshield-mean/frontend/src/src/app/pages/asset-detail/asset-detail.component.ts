import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ActivatedRoute } from '@angular/router';
import { GridshieldService } from '../../services/gridshield.service';
import { Asset } from '../../models/asset.model';
import { CauseLabelPipe } from '../../pipes/cause-label.pipe';

interface Factor { label: string; value: number; }

@Component({
  selector: 'app-asset-detail',
  standalone: true,
  imports: [CommonModule, FormsModule, CauseLabelPipe],
  template: `
    <div style="padding:28px 32px 48px;max-width:1000px">
      <div class="page-title">&#128269; Asset Detail</div>

      <div style="margin-bottom:18px;display:flex;align-items:center;gap:12px">
        <label style="font-size:0.85rem;color:var(--muted)">Select asset:</label>
        <select [(ngModel)]="selectedId" (change)="loadAsset()"
          style="padding:7px 12px;border:1px solid var(--border);border-radius:6px;font-size:0.9rem;background:#fff;min-width:160px">
          <option *ngFor="let id of assetIds" [value]="id">{{ id }}</option>
        </select>
      </div>

      <div *ngIf="loading" style="text-align:center;padding:40px"><span class="spinner"></span></div>
      <div *ngIf="error" style="color:var(--critical)">{{ error }}</div>

      <ng-container *ngIf="!loading && asset">
        <!-- Metrics -->
        <div class="metric-row">
          <div class="metric"><div class="mv">{{ asset.risk_score | number:'1.1-1' }} / 100</div><div class="ml">Risk Score</div></div>
          <div class="metric"><div class="mv">{{ asset.priority_score | number:'1.4-4' }}</div><div class="ml">Priority Score</div></div>
          <div class="metric"><div class="mv">{{ asset.estimated_intervention_cost | currency:'USD':'symbol':'1.0-0' }}</div><div class="ml">Intervention Cost</div></div>
          <div class="metric"><div class="mv">{{ asset.expected_loss | number:'1.1-1' }}</div><div class="ml">Expected Loss Index</div></div>
        </div>

        <!-- Info -->
        <div class="card">
          <div style="margin-bottom:8px">
            <strong>Risk Band:</strong>
            <span [class]="'badge badge-' + asset.risk_band" style="margin-left:6px">{{ asset.risk_band.toUpperCase() }}</span>
            &nbsp; <strong>Dominant Cause:</strong> <code>{{ asset.dominant_cause | causeLabel }}</code>
          </div>
          <div style="font-size:0.85rem;color:var(--muted)">
            <strong>Type:</strong> {{ asset.asset_type }} &nbsp;|&nbsp;
            <strong>Feeder:</strong> {{ asset.feeder_id }} &nbsp;|&nbsp;
            <strong>Critical Load:</strong> {{ asset.critical_loads }} &nbsp;|&nbsp;
            <strong>Customers:</strong> {{ asset.downstream_customers | number }} &nbsp;|&nbsp;
            <strong>Age:</strong> {{ asset.age_years }} yrs &nbsp;|&nbsp;
            <strong>Material:</strong> {{ asset.material }}
          </div>
        </div>

        <!-- Factor bar chart -->
        <div class="card">
          <h3>&#128200; Risk Score Breakdown (Contributing Factors)</h3>
          <div *ngFor="let f of factors" class="bar-row">
            <div class="bar-label">{{ f.label }}</div>
            <div class="bar-track">
              <div class="bar-fill" [style.width.%]="maxFactor > 0 ? (f.value / maxFactor * 100) : 0"></div>
            </div>
            <div class="bar-val">{{ f.value | number:'1.2-2' }}</div>
          </div>
          <p style="font-size:0.78rem;color:var(--muted);margin-top:8px">
            Total raw points: {{ totalFactors | number:'1.1-1' }} &rarr; capped risk score: {{ asset.risk_score | number:'1.1-1' }}
          </p>
        </div>

        <!-- Recommended action -->
        <div class="card">
          <h3>&#128203; Recommended Action</h3>
          <div [class]="'action-card action-' + asset.action_tier">
            <strong>Tier:</strong>
            <span [style.color]="tierColor(asset.action_tier)" style="font-weight:700;margin-left:4px">{{ asset.action_tier.toUpperCase() }}</span>
            <br><br>{{ asset.recommended_action }}
          </div>
          <p style="margin-top:10px;font-size:0.84rem"><strong>Crew:</strong> {{ asset.recommended_crew_type }}</p>
          <p style="font-size:0.84rem"><strong>Expected risk reduction after action:</strong> {{ asset.expected_risk_reduction_pct }}%</p>
          <div class="safety-box">&#9888; <strong>SAFETY NOTE</strong><br>{{ asset.safety_note }}</div>
        </div>
      </ng-container>

      <footer style="border-top:1px solid var(--border);padding:16px 0;text-align:center;font-size:0.75rem;color:var(--muted);margin-top:32px">Made with IBM Bob</footer>
    </div>
  `,
})
export class AssetDetailComponent implements OnInit {
  asset: Asset | null = null;
  assetIds: string[] = [];
  selectedId = '';
  loading = true;
  error = '';
  factors: Factor[] = [];
  maxFactor = 1;
  totalFactors = 0;

  constructor(private svc: GridshieldService, private route: ActivatedRoute) {}

  ngOnInit() {
    this.svc.getAssets().subscribe({
      next: (assets) => {
        this.assetIds  = assets.map(a => a.asset_id);
        const paramId  = this.route.snapshot.paramMap.get('id');
        this.selectedId = paramId && this.assetIds.includes(paramId) ? paramId : this.assetIds[0];
        this.loadAsset();
      },
      error: (e) => { this.error = e.message; this.loading = false; },
    });
  }

  loadAsset() {
    this.loading = true;
    this.svc.getAsset(this.selectedId).subscribe({
      next: (a) => {
        this.asset = a;
        this.factors = [
          { label: 'Wind',       value: a.factor_wind },
          { label: 'Rain',       value: a.factor_rain },
          { label: 'Tilt',       value: a.factor_tilt },
          { label: 'Erosion',    value: a.factor_erosion },
          { label: 'Corrosion',  value: a.factor_corrosion },
          { label: 'Drainage',   value: a.factor_drainage },
          { label: 'Vegetation', value: a.factor_vegetation },
          { label: 'Age',        value: a.factor_age },
        ].sort((x, y) => y.value - x.value);
        this.maxFactor    = Math.max(...this.factors.map(f => f.value), 1);
        this.totalFactors = this.factors.reduce((s, f) => s + f.value, 0);
        this.loading = false;
      },
      error: (e) => { this.error = e.message; this.loading = false; },
    });
  }

  tierColor(tier: string): string {
    const map: Record<string, string> = {
      immediate: 'var(--critical)',
      scheduled: 'var(--elevated)',
      monitor:   'var(--normal)',
    };
    return map[tier] || '#888';
  }
}

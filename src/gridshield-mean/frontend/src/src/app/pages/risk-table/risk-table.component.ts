import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { RouterLink } from '@angular/router';
import { GridshieldService } from '../../services/gridshield.service';
import { Asset } from '../../models/asset.model';
import { CauseLabelPipe } from '../../pipes/cause-label.pipe';

@Component({
  selector: 'app-risk-table',
  standalone: true,
  imports: [CommonModule, FormsModule, RouterLink, CauseLabelPipe],
  template: `
    <div style="padding:28px 32px 48px;max-width:1200px">
      <div class="page-title">&#128203; Ranked Asset Priority Queue</div>
      <div class="page-caption">Assets ranked by priority_score (risk &times; customer consequence &divide; intervention cost). Click column headers to sort.</div>

      <div *ngIf="loading" style="text-align:center;padding:40px"><span class="spinner"></span></div>
      <div *ngIf="error" style="color:var(--critical)">{{ error }}</div>

      <div *ngIf="!loading">
        <div class="filter-bar">
          <label>Band:
            <select [(ngModel)]="filterBand" (change)="applyFilter()">
              <option value="">All bands</option>
              <option *ngFor="let b of bands" [value]="b">{{ b }}</option>
            </select>
          </label>
          <label>Type:
            <select [(ngModel)]="filterType" (change)="applyFilter()">
              <option value="">All types</option>
              <option *ngFor="let t of types" [value]="t">{{ t }}</option>
            </select>
          </label>
          <label>Feeder:
            <select [(ngModel)]="filterFeeder" (change)="applyFilter()">
              <option value="">All feeders</option>
              <option *ngFor="let f of feeders" [value]="f">{{ f }}</option>
            </select>
          </label>
          <label>Search:
            <input type="text" [(ngModel)]="search" (input)="applyFilter()" placeholder="Asset ID..." />
          </label>
        </div>

        <div class="table-wrap">
          <table>
            <thead>
              <tr>
                <th (click)="sortBy('asset_id')" style="cursor:pointer">Asset &#8597;</th>
                <th (click)="sortBy('asset_type')" style="cursor:pointer">Type &#8597;</th>
                <th (click)="sortBy('risk_band')" style="cursor:pointer">Band &#8597;</th>
                <th (click)="sortBy('risk_score')" style="cursor:pointer">Risk &#8597;</th>
                <th (click)="sortBy('priority_score')" style="cursor:pointer">Priority &#8597;</th>
                <th (click)="sortBy('expected_loss')" style="cursor:pointer">Exp. Loss &#8597;</th>
                <th (click)="sortBy('estimated_intervention_cost')" style="cursor:pointer">Cost &#8597;</th>
                <th (click)="sortBy('dominant_cause')" style="cursor:pointer">Cause &#8597;</th>
                <th (click)="sortBy('action_tier')" style="cursor:pointer">Tier &#8597;</th>
                <th (click)="sortBy('downstream_customers')" style="cursor:pointer">Customers &#8597;</th>
              </tr>
            </thead>
            <tbody>
              <tr *ngFor="let a of filtered"
                  [class]="'tint-' + a.risk_band" style="cursor:pointer"
                  [routerLink]="['/asset', a.asset_id]">
                <td><strong>{{ a.asset_id }}</strong></td>
                <td>{{ a.asset_type }}</td>
                <td><span [class]="'badge badge-' + a.risk_band">{{ a.risk_band.toUpperCase() }}</span></td>
                <td>{{ a.risk_score | number:'1.1-1' }}</td>
                <td>{{ a.priority_score | number:'1.5-5' }}</td>
                <td>{{ a.expected_loss | number:'1.1-1' }}</td>
                <td>{{ a.estimated_intervention_cost | currency:'USD':'symbol':'1.0-0' }}</td>
                <td>{{ a.dominant_cause | causeLabel }}</td>
                <td><span [class]="'tier-badge tier-' + a.action_tier">{{ a.action_tier }}</span></td>
                <td>{{ a.downstream_customers | number }}</td>
              </tr>
            </tbody>
          </table>
        </div>
        <p style="margin-top:8px;font-size:0.8rem;color:var(--muted)">Showing {{ filtered.length }} of {{ all.length }} assets.</p>
      </div>

      <footer style="border-top:1px solid var(--border);padding:16px 0;text-align:center;font-size:0.75rem;color:var(--muted);margin-top:32px">Made with IBM Bob</footer>
    </div>
  `,
})
export class RiskTableComponent implements OnInit {
  all: Asset[] = [];
  filtered: Asset[] = [];
  loading = true;
  error = '';

  filterBand   = '';
  filterType   = '';
  filterFeeder = '';
  search       = '';

  bands   = ['critical','elevated','watch','normal'];
  types:   string[] = [];
  feeders: string[] = [];

  sortCol: keyof Asset = 'priority_score';
  sortDir = -1;

  constructor(private svc: GridshieldService) {}

  ngOnInit() {
    this.svc.getAssets().subscribe({
      next: (a) => {
        this.all     = a;
        this.types   = [...new Set(a.map(x => x.asset_type))].sort();
        this.feeders = [...new Set(a.map(x => x.feeder_id))].sort();
        this.applyFilter();
        this.loading = false;
      },
      error: (e) => { this.error = e.message; this.loading = false; },
    });
  }

  applyFilter() {
    this.filtered = this.all.filter(a =>
      (!this.filterBand   || a.risk_band   === this.filterBand)   &&
      (!this.filterType   || a.asset_type  === this.filterType)   &&
      (!this.filterFeeder || a.feeder_id   === this.filterFeeder) &&
      (!this.search       || a.asset_id.toLowerCase().includes(this.search.toLowerCase()))
    );
    this.doSort();
  }

  sortBy(col: keyof Asset) {
    if (this.sortCol === col) this.sortDir *= -1; else { this.sortCol = col; this.sortDir = -1; }
    this.doSort();
  }

  doSort() {
    const col = this.sortCol;
    const dir = this.sortDir;
    this.filtered = [...this.filtered].sort((a, b) => {
      const av = a[col] as number | string;
      const bv = b[col] as number | string;
      return av > bv ? dir : av < bv ? -dir : 0;
    });
  }
}

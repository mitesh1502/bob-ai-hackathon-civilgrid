import { Routes } from '@angular/router';
import { DashboardComponent }   from './pages/dashboard/dashboard.component';
import { RiskTableComponent }   from './pages/risk-table/risk-table.component';
import { AssetDetailComponent } from './pages/asset-detail/asset-detail.component';
import { ReactiveComponent }    from './pages/reactive/reactive.component';
import { AdvisorComponent }     from './pages/advisor/advisor.component';

export const routes: Routes = [
  { path: '',           redirectTo: 'dashboard', pathMatch: 'full' },
  { path: 'dashboard',  component: DashboardComponent },
  { path: 'risk-table', component: RiskTableComponent },
  { path: 'asset/:id',  component: AssetDetailComponent },
  { path: 'reactive',   component: ReactiveComponent },
  { path: 'advisor',    component: AdvisorComponent },
  { path: '**',         redirectTo: 'dashboard' },
];

import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { Asset, Stats, Incident } from '../models/asset.model';

@Injectable({ providedIn: 'root' })
export class GridshieldService {
  private base = '/api';

  constructor(private http: HttpClient) {}

  getAssets(): Observable<Asset[]> {
    return this.http.get<Asset[]>(`${this.base}/assets`);
  }

  getAsset(id: string): Observable<Asset> {
    return this.http.get<Asset>(`${this.base}/assets/${id}`);
  }

  getStats(): Observable<Stats> {
    return this.http.get<Stats>(`${this.base}/assets/stats`);
  }

  getIncidents(): Observable<Incident[]> {
    return this.http.get<Incident[]>(`${this.base}/pipeline/incidents`);
  }

  runPipeline(): Observable<{ success: boolean; message: string }> {
    return this.http.post<{ success: boolean; message: string }>(
      `${this.base}/pipeline/run`, {}
    );
  }

  ask(question: string): Observable<{ answer: string }> {
    return this.http.post<{ answer: string }>(`${this.base}/advisor/ask`, { question });
  }
}

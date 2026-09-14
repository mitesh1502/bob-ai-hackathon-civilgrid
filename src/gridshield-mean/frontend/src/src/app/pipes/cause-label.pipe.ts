import { Pipe, PipeTransform } from '@angular/core';

/** Converts snake_case dominant_cause to human-readable "flood drainage" */
@Pipe({ name: 'causeLabel', standalone: true })
export class CauseLabelPipe implements PipeTransform {
  transform(value: string): string {
    return (value || '').replace(/_/g, ' ');
  }
}

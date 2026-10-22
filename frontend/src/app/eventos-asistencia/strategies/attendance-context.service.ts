import { Injectable } from '@angular/core';
import { BehaviorSubject, Observable } from 'rxjs';
import { MetodoCapturaAsistencia } from '../models/eventos-asistencia.models';
import { IAttendanceCaptureStrategy } from './attendance-strategy.interface';
import { ManualAttendanceStrategy } from './manual-attendance.strategy';
import { BiometricAttendanceStrategy } from './biometric-attendance.strategy';

@Injectable({
  providedIn: 'root'
})
export class AttendanceContextService {
  private strategySubject: BehaviorSubject<IAttendanceCaptureStrategy>;
  public currentStrategy$: Observable<IAttendanceCaptureStrategy>;

  constructor(
    private manualStrategy: ManualAttendanceStrategy,
    private biometricStrategy: BiometricAttendanceStrategy
  ) {
    this.strategySubject = new BehaviorSubject<IAttendanceCaptureStrategy>(this.manualStrategy);
    this.currentStrategy$ = this.strategySubject.asObservable();
  }

  get currentStrategy(): IAttendanceCaptureStrategy {
    return this.strategySubject.value;
  }

  setStrategy(tipo: MetodoCapturaAsistencia): IAttendanceCaptureStrategy {
    const selected = tipo === 'BIOMETRICO' ? this.biometricStrategy : this.manualStrategy;
    this.strategySubject.next(selected);
    return selected;
  }
}

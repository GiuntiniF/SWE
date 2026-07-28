---
source: domain_model.gaphor
sourceHash: sha256:9651193765cfbff5
generator: gaphor2md
---

# Modello: domain_model

Strato semantico generato automaticamente dal file Gaphor. Non modificare a mano: rigenerare con `gaphor2md.py`.

| Tipo | Conteggio |
| --- | --- |
| Association | 8 |
| Class | 41 |
| ClassDiagram | 1 |
| DataType | 2 |
| Dependency | 14 |
| Diagram | 1 |
| Enumeration | 4 |
| Generalization | 18 |
| Interface | 6 |
| InterfaceRealization | 13 |
| Package | 7 |
| Usage | 16 |

## Diagrammi

### _BusinessLogic — *classi*

_Nessun elemento semantico._

### _Domain Model — *generico*

- **Association**: Athlete — BookingRequest, CoachingSession — Athlete, exercises (WorkoutActivity — TrainingSession), HIIT — CardioActivity, Superset — WeightActivity, trainingPlans (TrainingPlan — Athlete), trainingSessions (TrainingSession — TrainingPlan), trainingSessions (TrainingSession — TrainingPlanTemplate)
- **Class**: Athlete, BookingRequest, CaloriesTarget, CaloriesTargetFactory, Cardio, CardioIntensityFactory, CardioTargetFactory, CoachingSession, DistanceTarget, DistanceTargetFactory, DropSetDecorator, DurationTarget, DurationTargetFactory, Exercise, FailureReps, FailureRepsFactory, FixedReps, FixedRepsFactory, FIxedWeight, FixedWeightFactory, HeartRateIntensity, HeartRateIntensityFactory, HIIT, MachineSettingsIntensity, MachineSettingsIntensityFactory, PercentageWeight, PercentageWeightFactory, PT, RangeReps, RangeRepsFactory, RepsFactory, RestPauseDecorator, Superset, TrainingPlan, TrainingPlanBuilder, TrainingPlanTemplate, TrainingSession, User, Weight, WeightActivityDecorator, WeightFactory
- **DataType**: ExerciseType, Gym
- **Dependency**: <<create>> (TrainingPlanBuilder → TrainingPlan), <<use>> (TrainingPlan → TrainingPlanStatus), <<use>> (TrainingPlanBuilder → TrainingPlanTemplate), DistanceTarget → DistanceUnit, «instantiate» (CaloriesTargetFactory → CaloriesTarget), «instantiate» (DistanceTargetFactory → DistanceTarget), «instantiate» (DurationTargetFactory → DurationTarget), «instantiate» (FailureRepsFactory → FailureReps), «instantiate» (FixedRepsFactory → FixedReps), «instantiate» (FixedWeightFactory → FIxedWeight), «instantiate» (HeartRateIntensityFactory → MachineSettingsIntensity), «instantiate» (MachineSettingsIntensityFactory → HeartRateIntensity), «instantiate» (PercentageWeightFactory → PercentageWeight), «instantiate» (RangeRepsFactory → RangeReps)
- **Enumeration**: BookingStatus, DistanceUnit, TrainingPlanStatus, WeightMeasureUnit
- **Generalization**: Athlete → User, CaloriesTargetFactory → CardioTargetFactory, CardioActivity → WorkoutActivity, DistanceTargetFactory → CardioTargetFactory, DropSetDecorator → WeightActivityDecorator, DurationTargetFactory → CardioTargetFactory, FailureRepsFactory → RepsFactory, FixedRepsFactory → RepsFactory, FIxedWeight → Weight, FixedWeightFactory → WeightFactory, HeartRateIntensityFactory → CardioIntensityFactory, MachineSettingsIntensityFactory → CardioIntensityFactory, PercentageWeight → Weight, PercentageWeightFactory → WeightFactory, PT → User, RangeRepsFactory → RepsFactory, RestPauseDecorator → WeightActivityDecorator, WeightActivity → WorkoutActivity
- **Interface**: CardioActivity, CardioIntensity, CardioTarget, Reps, WeightActivity, WorkoutActivity
- **InterfaceRealization**: CaloriesTarget → CardioTarget, Cardio → CardioActivity, DistanceTarget → CardioTarget, DurationTarget → CardioTarget, Exercise → WeightActivity, FailureReps → Reps, FixedReps → Reps, HeartRateIntensity → CardioIntensity, HIIT → CardioActivity, MachineSettingsIntensity → CardioIntensity, RangeReps → Reps, Superset → WeightActivity, WeightActivityDecorator → WeightActivity
- **Package**: Coaching, Exercises, TrainingPlan, User
- **Usage**: Athlete → Gym, BookingRequest → BookingStatus, BookingRequest → Usage[CoachingSession → Gym], Cardio → CardioTarget, CardioIntensityFactory → CardioIntensity, CardioTargetFactory → CardioTarget, CoachingSession → Gym, Exercise → Reps, PercentageWeight → Usage[PercentageWeightFactory → WeightMeasureUnit], PercentageWeightFactory → WeightMeasureUnit, RepsFactory → Reps, Superset → ExerciseType, Usage[Cardio → CardioTarget] → CardioIntensity, Usage[Exercise → Reps] → Weight, WeightActivity → ExerciseType, WeightFactory → Weight

## Elementi

### Package `App PT / Domain Model`

#### DataType `Gym`

**Attributi**

| Vis | Nome | Tipo | Molt. | Default | Note |
| --- | --- | --- | --- | --- | --- |
| - | name | string | — | — | — |
| - | address | Address | — | — | — |
| - | phone | string | — | — | — |
| - | athleteList | Athlete | 1..* | — | — |

### Package `App PT / Domain Model / Coaching`

#### Class `BookingRequest`

**Attributi**

| Vis | Nome | Tipo | Molt. | Default | Note |
| --- | --- | --- | --- | --- | --- |
| - | athleteId | int | — | — | — |
| - | status | BookingStatus | — | — | — |
| - | proposedDatetime | LocalDateTime | — | — | — |
| - | reasonForSession | string | — | — | — |
| - | gym | Gym | — | — | — |

#### Class `CoachingSession`

**Attributi**

| Vis | Nome | Tipo | Molt. | Default | Note |
| --- | --- | --- | --- | --- | --- |
| - | athleteId | int | — | — | — |
| - | status | BookingStatus | — | — | — |
| - | datetime | LocalDateTime | — | — | — |
| - | reasonForSession | string | — | — | — |
| - | gym | Gym | — | — | — |

#### Enumeration `BookingStatus`

**Valori**: `pending`, `confirmed`, `cancelled`

### Package `App PT / Domain Model / Exercises`

#### Class `CaloriesTarget`

**Attributi**

| Vis | Nome | Tipo | Molt. | Default | Note |
| --- | --- | --- | --- | --- | --- |
| + | calories | int | — | — | — |

**Operazioni**

| Vis | Firma | Ritorno | Note |
| --- | --- | --- | --- |
| + | getTargetDisplay() | void | — |

#### Class `CaloriesTargetFactory`

**Operazioni**

| Vis | Firma | Ritorno | Note |
| --- | --- | --- | --- |
| + | createTarget() | CaloriesTarget | — |

#### Class `Cardio`

**Attributi**

| Vis | Nome | Tipo | Molt. | Default | Note |
| --- | --- | --- | --- | --- | --- |
| - | target | CardioTarget | — | — | — |
| - | intensity | CardioIntensity | — | — | — |

**Operazioni**

| Vis | Firma | Ritorno | Note |
| --- | --- | --- | --- |
| + | getCalories() | int | — |
| + | getTargetDisplay() | string | — |
| + | getIntensityDisplay() | string | — |

#### Class `CardioIntensityFactory`

**Operazioni**

| Vis | Firma | Ritorno | Note |
| --- | --- | --- | --- |
| + | + createIntensityFromPayload(cardioTargetData): CardioIntensity: ()() | void | — |
| + | createIntensity() | void | abstract |

#### Class `CardioTargetFactory`

**Operazioni**

| Vis | Firma | Ritorno | Note |
| --- | --- | --- | --- |
| + | + createTargetFromPayload(cardioTargetData): CardioTarget: ()() | void | — |
| + | createTarget() | void | — |

#### Class `DistanceTarget`

**Attributi**

| Vis | Nome | Tipo | Molt. | Default | Note |
| --- | --- | --- | --- | --- | --- |
| + | distanceValue | float | — | — | — |
| + | distanceUnit | DistanceUnit | — | — | — |

**Operazioni**

| Vis | Firma | Ritorno | Note |
| --- | --- | --- | --- |
| + | getTargetDisplay() | void | — |

#### Class `DistanceTargetFactory`

**Operazioni**

| Vis | Firma | Ritorno | Note |
| --- | --- | --- | --- |
| + | createTarget() | DistanceTarget | — |

#### Class `DropSetDecorator`

NOTA: di fatto non ha senso se le reps non sono di tipo FailureReps ma lo si permette per flessibilità

**Attributi**

| Vis | Nome | Tipo | Molt. | Default | Note |
| --- | --- | --- | --- | --- | --- |
| + | dropRepsWeightMultiplier | float | — | — | — |

**Operazioni**

| Vis | Firma | Ritorno | Note |
| --- | --- | --- | --- |
| + | getVolumeValue() | int | — |
| + | getVolumeDisplay() | string | — |

#### Class `DurationTarget`

**Attributi**

| Vis | Nome | Tipo | Molt. | Default | Note |
| --- | --- | --- | --- | --- | --- |
| + | minutes | Duration | — | — | — |

**Operazioni**

| Vis | Firma | Ritorno | Note |
| --- | --- | --- | --- |
| + | getTargetDisplay() | string | — |

#### Class `DurationTargetFactory`

**Operazioni**

| Vis | Firma | Ritorno | Note |
| --- | --- | --- | --- |
| + | createTarget() | DurationTarget | — |

#### Class `Exercise`

NOTE
reps = -1 -> cedimento

**Attributi**

| Vis | Nome | Tipo | Molt. | Default | Note |
| --- | --- | --- | --- | --- | --- |
| - | sets | int | — | — | — |
| - | reps | Reps | — | — | — |
| - | weight | Weight | — | — | — |
| - | restTime | Duration | — | — | — |
| + | exerciseType | ExerciseType | — | — | — |

**Operazioni**

| Vis | Firma | Ritorno | Note |
| --- | --- | --- | --- |
| + | getVolumeValue() | int | — |
| + | getRestTime() | int | — |

#### Class `FailureReps`

**Operazioni**

| Vis | Firma | Ritorno | Note |
| --- | --- | --- | --- |
| + | getVolumeValue() | int | — |
| + | getDisplayValue() | string | — |
| + | isToFailure() | bool | — |

#### Class `FailureRepsFactory`

**Operazioni**

| Vis | Firma | Ritorno | Note |
| --- | --- | --- | --- |
| + | createReps() | Reps | — |

#### Class `FixedReps`

**Attributi**

| Vis | Nome | Tipo | Molt. | Default | Note |
| --- | --- | --- | --- | --- | --- |
| - | repsNumber | int | — | — | — |

**Operazioni**

| Vis | Firma | Ritorno | Note |
| --- | --- | --- | --- |
| + | getVolumeValue() | int | — |
| + | getDisplayValue() | string | — |
| + | isToFailure() | bool | — |

#### Class `FixedRepsFactory`

**Operazioni**

| Vis | Firma | Ritorno | Note |
| --- | --- | --- | --- |
| + | createReps() | Reps | — |

#### Class `FIxedWeight`

**Attributi**

| Vis | Nome | Tipo | Molt. | Default | Note |
| --- | --- | --- | --- | --- | --- |
| - | weightValue | float | — | — | — |
| - | weightMeasureUnit | WeightMeasureUnit | — | — | — |

**Operazioni**

| Vis | Firma | Ritorno | Note |
| --- | --- | --- | --- |
| + | getLoadValue() | float | — |
| + | () | void | — |

#### Class `FixedWeightFactory`

**Attributi**

| Vis | Nome | Tipo | Molt. | Default | Note |
| --- | --- | --- | --- | --- | --- |
| - | weightValue | float | — | — | — |
| - | weightMeasureUnit | WeightMeasureUnit | — | — | — |

**Operazioni**

| Vis | Firma | Ritorno | Note |
| --- | --- | --- | --- |
| + | createWeight() | Weight | — |

#### Class `HeartRateIntensity`

**Attributi**

| Vis | Nome | Tipo | Molt. | Default | Note |
| --- | --- | --- | --- | --- | --- |
| + | zone | HeartRateZone | — | — | — |
| + | value | int | — | — | — |

**Operazioni**

| Vis | Firma | Ritorno | Note |
| --- | --- | --- | --- |
| + | getTargetDisplay() | void | — |

#### Class `HeartRateIntensityFactory`

**Operazioni**

| Vis | Firma | Ritorno | Note |
| --- | --- | --- | --- |
| + | createTarget() | HeartRateIntensity | — |

#### Class `HIIT`

**Attributi**

| Vis | Nome | Tipo | Molt. | Default | Note |
| --- | --- | --- | --- | --- | --- |
| + | intervals | CardioActivity | 1..* | — | — |

**Operazioni**

| Vis | Firma | Ritorno | Note |
| --- | --- | --- | --- |
| + | getCalories() | int | — |
| + | getTargetDisplay() | string | — |
| + | getIntensityDisplay() | string | — |

#### Class `MachineSettingsIntensity`

**Attributi**

| Vis | Nome | Tipo | Molt. | Default | Note |
| --- | --- | --- | --- | --- | --- |
| - | speed | float | — | — | — |
| - | incline | float | — | — | — |
| - | level | float | — | — | — |

**Operazioni**

| Vis | Firma | Ritorno | Note |
| --- | --- | --- | --- |
| + | getTargetDisplay() | string | — |

#### Class `MachineSettingsIntensityFactory`

**Operazioni**

| Vis | Firma | Ritorno | Note |
| --- | --- | --- | --- |
| + | createTarget() | MachineSettingsIntensity | — |

#### Class `PercentageWeight`

**Attributi**

| Vis | Nome | Tipo | Molt. | Default | Note |
| --- | --- | --- | --- | --- | --- |
| - | oneRepMaximum | float | — | — | — |
| - | weightPercentage | float | — | — | — |
| - | weightMeasureUnit | WeightMeasureUnit | — | — | — |

**Operazioni**

| Vis | Firma | Ritorno | Note |
| --- | --- | --- | --- |
| + | getLoadValue() | float | — |
| + | () | void | — |

#### Class `PercentageWeightFactory`

**Attributi**

| Vis | Nome | Tipo | Molt. | Default | Note |
| --- | --- | --- | --- | --- | --- |
| - | oneRepMaximum | float | — | — | — |
| - | weightPercentage | float | — | — | — |
| - | weightMeasureUnit | WeightMeasureUnit | — | — | — |

**Operazioni**

| Vis | Firma | Ritorno | Note |
| --- | --- | --- | --- |
| + | createWeight() | Weight | — |

#### Class `RangeReps`

**Attributi**

| Vis | Nome | Tipo | Molt. | Default | Note |
| --- | --- | --- | --- | --- | --- |
| - | minReps | int | — | — | — |
| - | maxReps | int | — | — | — |

**Operazioni**

| Vis | Firma | Ritorno | Note |
| --- | --- | --- | --- |
| + | getVolumeValue() | int | — |
| + | getDIsplayValue() | string | — |
| + | isToFailure() | bool | — |

#### Class `RangeRepsFactory`

**Operazioni**

| Vis | Firma | Ritorno | Note |
| --- | --- | --- | --- |
| + | createReps() | Reps | — |

#### Class `RepsFactory`

**Operazioni**

| Vis | Firma | Ritorno | Note |
| --- | --- | --- | --- |
| + | createRepsFromPayload(repsData) | Reps | — |
| + | createReps() | Reps | — |

#### Class `RestPauseDecorator`

**Attributi**

| Vis | Nome | Tipo | Molt. | Default | Note |
| --- | --- | --- | --- | --- | --- |
| + | restTimeBetweenReps | Duration | — | — | — |

**Operazioni**

| Vis | Firma | Ritorno | Note |
| --- | --- | --- | --- |
| + | getRestTypeBetweenReps() | void | — |

#### Class `Superset`

**Attributi**

| Vis | Nome | Tipo | Molt. | Default | Note |
| --- | --- | --- | --- | --- | --- |
| - | exercises | ExerciseInterface | 1..* | — | — |

**Operazioni**

| Vis | Firma | Ritorno | Note |
| --- | --- | --- | --- |
| + | getVolumeValue() | int | — |
| + | getRestTime() | Duration | — |
| + | getExerciseType() | ExerciseType | — |
| + | getVolumeDisplay() | string | — |

#### Class `Weight`

**Attributi**

| Vis | Nome | Tipo | Molt. | Default | Note |
| --- | --- | --- | --- | --- | --- |
| + | weightMeasureUnit | WeightMeasureUnit | — | — | — |

**Operazioni**

| Vis | Firma | Ritorno | Note |
| --- | --- | --- | --- |
| + | getLoadValue() | float | — |
| + | () | void | — |

#### Class `WeightActivityDecorator`

**Operazioni**

| Vis | Firma | Ritorno | Note |
| --- | --- | --- | --- |
| + | getVolumeValue() | void | — |
| + | getVolumeDisplay() | void | — |
| + | getRestTime() | void | — |
| + | getExerciseType() | void | — |

#### Class `WeightFactory`

**Operazioni**

| Vis | Firma | Ritorno | Note |
| --- | --- | --- | --- |
| + | createWeight() | void | — |
| + | + createWeightFromPayload(weightData): Weight)()() | void | — |

#### DataType `ExerciseType`

**Attributi**

| Vis | Nome | Tipo | Molt. | Default | Note |
| --- | --- | --- | --- | --- | --- |
| + | name | string | — | — | — |
| + | description | string | — | — | — |
| + | targetMuscleGroup | string | — | — | — |
| + | musclesInvolved | string | 0..* | — | — |

#### Enumeration `DistanceUnit`

**Valori**: `Km`, `m`, `mi`

#### Enumeration `WeightMeasureUnit`

**Valori**: `KG`, `Lbs`, `BodyWeight`

#### Interface `CardioActivity`

**Operazioni**

| Vis | Firma | Ritorno | Note |
| --- | --- | --- | --- |
| + | getCalories() | int | — |
| + | getTarget() | void | — |
| + | getIntensity() | void | — |

#### Interface `CardioIntensity`

**Operazioni**

| Vis | Firma | Ritorno | Note |
| --- | --- | --- | --- |
| + | getDisplay() | string | — |

#### Interface `CardioTarget`

**Operazioni**

| Vis | Firma | Ritorno | Note |
| --- | --- | --- | --- |
| + | getTargetDisplay() | string | — |

#### Interface `Reps`

**Operazioni**

| Vis | Firma | Ritorno | Note |
| --- | --- | --- | --- |
| + | getVolumeValue() | int | — |
| + | getDisplayValue() | string | — |
| + | isToFailure() | boolean | — |

#### Interface `WeightActivity`

**Attributi**

| Vis | Nome | Tipo | Molt. | Default | Note |
| --- | --- | --- | --- | --- | --- |
| + | + getCalories(): int | — | — | — | — |
| + | + getVolume() | — | — | — | — |
| + | + getRestTime() | — | — | — | — |
| + | getExerciseType() | — | — | — | — |
| + | getExecutionNotes(): string | — | — | — | — |
| + | getVolumeDisplay() | — | — | — | — |

#### Interface `WorkoutActivity`

**Operazioni**

| Vis | Firma | Ritorno | Note |
| --- | --- | --- | --- |
| + | getCalories() | int | — |

### Package `App PT / Domain Model / TrainingPlan`

#### Class `TrainingPlan`

**Attributi**

| Vis | Nome | Tipo | Molt. | Default | Note |
| --- | --- | --- | --- | --- | --- |
| - | name | string | — | — | — |
| - | description | string | — | — | — |
| - | startDate | LocalDate | — | — | — |
| - | numberOfMonths | int | — | — | — |
| - | athleteId | int | — | — | — |
| - | status | TrainingPlanStatus | — | — | — |
| - | trainingSessions | TrainingSessions | 0..7 | — | — |

#### Class `TrainingPlanBuilder`

**Attributi**

| Vis | Nome | Tipo | Molt. | Default | Note |
| --- | --- | --- | --- | --- | --- |
| - | name | string | — | — | — |
| - | startDate | LocalDate | — | — | — |
| - | numberOfMonths | int | — | — | — |
| - | athleteId | int | — | — | — |

**Operazioni**

| Vis | Firma | Ritorno | Note |
| --- | --- | --- | --- |
| + | withName(title: string) | Builder | — |
| + | withDescription(desc: string) | Builder | — |
| + | forAthlete(athleteItd: int) | Builder | — |
| + | fromDate(startdate: localDate) | Builder | — |
| + | forMonths(numberOfMonths: int) | Builder | — |
| + | fromTemplate(planTemplate: TrainingPlanTemplate) | Builder | — |
| + | build() | TrainingPlan | — |

#### Class `TrainingPlanTemplate`

**Attributi**

| Vis | Nome | Tipo | Molt. | Default | Note |
| --- | --- | --- | --- | --- | --- |
| - | name | string | — | — | — |
| - | description | string | — | — | — |
| - | trainingSessions | TrainingSession | 0..7 | — | — |

#### Class `TrainingSession`

**Attributi**

| Vis | Nome | Tipo | Molt. | Default | Note |
| --- | --- | --- | --- | --- | --- |
| - | exercises | WorkoutActivity | 1..* | — | — |

**Operazioni**

| Vis | Firma | Ritorno | Note |
| --- | --- | --- | --- |
| + | getTotalCalories() | int | — |
| + | getTotalVolume() | void | — |
| + | getTotalLoad() | void | — |

#### Enumeration `TrainingPlanStatus`

**Valori**: `Draft`, `Completed`, `Deleted`

### Package `App PT / Domain Model / User`

#### Class `Athlete`

**Attributi**

| Vis | Nome | Tipo | Molt. | Default | Note |
| --- | --- | --- | --- | --- | --- |
| - | height | float | — | — | — |
| - | weight | float | — | — | — |
| - | gymList | Gym | 0..* | — | — |
| - | trainingPlans | TrainingPlan | 0..* | — | — |
| - | coachingSessions | CoachingSessions | 0..* | — | — |
| - | bookingRequests | BOokingRequest | 0..* | — | — |

**Operazioni**

| Vis | Firma | Ritorno | Note |
| --- | --- | --- | --- |
| + | getAge() | int | — |

#### Class `PT`

#### Class `User`

**Attributi**

| Vis | Nome | Tipo | Molt. | Default | Note |
| --- | --- | --- | --- | --- | --- |
| - | firstName | string | — | — | — |
| - | lastName | string | — | — | — |
| - | birthDate | LocalDate | — | — | — |
| - | email | string | — | — | — |
| - | hashedPassword | string | — | — | — |

## Relazioni

| Tipo | Origine | Destinazione | Dettagli |
| --- | --- | --- | --- |
| Association | Athlete [0..1] | BookingRequest [0..*] | aggregazione lato BookingRequest |
| Association | CoachingSession [0..*] | Athlete [0..1] | aggregazione lato CoachingSession |
| Association | HIIT [0..1] | CardioActivity [1..*] | aggregazione lato CardioActivity |
| Association | Superset [0..1] | WeightActivity [1..*] | aggregazione lato WeightActivity |
| Association | TrainingPlan [0..*] | Athlete [0..1] | nome: trainingPlans; aggregazione lato TrainingPlan |
| Association | TrainingSession [0..7] | TrainingPlan [0..1] | nome: trainingSessions; aggregazione lato TrainingSession |
| Association | TrainingSession [0..7] | TrainingPlanTemplate [0..1] | nome: trainingSessions; aggregazione lato TrainingSession |
| Association | WorkoutActivity [1..*] | TrainingSession [0..1] | nome: exercises; aggregazione lato WorkoutActivity |
| Dependency | CaloriesTargetFactory | CaloriesTarget | nome: «instantiate» |
| Dependency | DistanceTarget | DistanceUnit | — |
| Dependency | DistanceTargetFactory | DistanceTarget | nome: «instantiate» |
| Dependency | DurationTargetFactory | DurationTarget | nome: «instantiate» |
| Dependency | FailureRepsFactory | FailureReps | nome: «instantiate» |
| Dependency | FixedRepsFactory | FixedReps | nome: «instantiate» |
| Dependency | FixedWeightFactory | FIxedWeight | nome: «instantiate» |
| Dependency | HeartRateIntensityFactory | MachineSettingsIntensity | nome: «instantiate» |
| Dependency | MachineSettingsIntensityFactory | HeartRateIntensity | nome: «instantiate» |
| Dependency | PercentageWeightFactory | PercentageWeight | nome: «instantiate» |
| Dependency | RangeRepsFactory | RangeReps | nome: «instantiate» |
| Dependency | TrainingPlan | TrainingPlanStatus | nome: <<use>> |
| Dependency | TrainingPlanBuilder | TrainingPlan | nome: <<create>> |
| Dependency | TrainingPlanBuilder | TrainingPlanTemplate | nome: <<use>> |
| Generalization | Athlete | User | — |
| Generalization | CaloriesTargetFactory | CardioTargetFactory | — |
| Generalization | CardioActivity | WorkoutActivity | — |
| Generalization | DistanceTargetFactory | CardioTargetFactory | — |
| Generalization | DropSetDecorator | WeightActivityDecorator | — |
| Generalization | DurationTargetFactory | CardioTargetFactory | — |
| Generalization | FIxedWeight | Weight | — |
| Generalization | FailureRepsFactory | RepsFactory | — |
| Generalization | FixedRepsFactory | RepsFactory | — |
| Generalization | FixedWeightFactory | WeightFactory | — |
| Generalization | HeartRateIntensityFactory | CardioIntensityFactory | — |
| Generalization | MachineSettingsIntensityFactory | CardioIntensityFactory | — |
| Generalization | PT | User | — |
| Generalization | PercentageWeight | Weight | — |
| Generalization | PercentageWeightFactory | WeightFactory | — |
| Generalization | RangeRepsFactory | RepsFactory | — |
| Generalization | RestPauseDecorator | WeightActivityDecorator | — |
| Generalization | WeightActivity | WorkoutActivity | — |
| InterfaceRealization | CaloriesTarget | CardioTarget | — |
| InterfaceRealization | Cardio | CardioActivity | — |
| InterfaceRealization | DistanceTarget | CardioTarget | — |
| InterfaceRealization | DurationTarget | CardioTarget | — |
| InterfaceRealization | Exercise | WeightActivity | — |
| InterfaceRealization | FailureReps | Reps | — |
| InterfaceRealization | FixedReps | Reps | — |
| InterfaceRealization | HIIT | CardioActivity | — |
| InterfaceRealization | HeartRateIntensity | CardioIntensity | — |
| InterfaceRealization | MachineSettingsIntensity | CardioIntensity | — |
| InterfaceRealization | RangeReps | Reps | — |
| InterfaceRealization | Superset | WeightActivity | — |
| InterfaceRealization | WeightActivityDecorator | WeightActivity | — |
| Usage | Athlete | Gym | — |
| Usage | BookingRequest | BookingStatus | — |
| Usage | BookingRequest | Usage[CoachingSession → Gym] | — |
| Usage | Cardio | CardioTarget | — |
| Usage | CardioIntensityFactory | CardioIntensity | — |
| Usage | CardioTargetFactory | CardioTarget | — |
| Usage | CoachingSession | Gym | — |
| Usage | Exercise | Reps | — |
| Usage | PercentageWeight | Usage[PercentageWeightFactory → WeightMeasureUnit] | — |
| Usage | PercentageWeightFactory | WeightMeasureUnit | — |
| Usage | RepsFactory | Reps | — |
| Usage | Superset | ExerciseType | — |
| Usage | Usage[Cardio → CardioTarget] | CardioIntensity | — |
| Usage | Usage[Exercise → Reps] | Weight | — |
| Usage | WeightActivity | ExerciseType | — |
| Usage | WeightFactory | Weight | — |

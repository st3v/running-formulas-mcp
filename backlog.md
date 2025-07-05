# Running Calculator MCP - Feature Backlog

This document outlines potential additional running-related calculations that could be added to the MCP server to expand its functionality beyond the current functionality.

## Current Features
- ✅ VDOT Calculation (Jack Daniels formula)
- ✅ Training Pace Recommendations (Easy, Marathon, Threshold, Interval, Repetition)
- ✅ Race Time Predictions (Riegel's formula + Daniels' VDOT method)
- ✅ Pace Conversions (min/km ↔ min/mile ↔ mph ↔ km/h)

## Proposed Additional Features

### 1. Training Zone Calculator (Heart Rate)
**Priority: Medium**
- Calculate heart rate zones based on max HR or lactate threshold
- Different methodologies, including the Karvonen Formula, percentage of max HR, etc.
- **Input:** max HR or resting HR + max HR
- **Output:** HR zones for different training intensities
- **Use Case:** Setting up heart rate monitor zones for training

### 3. VO2 Max Estimation
**Priority: Medium**
- Estimate VO2 max from race performances
- Multiple formulas available (Jack Daniels, Mercier, etc.)
- **Input:** race distance and time
- **Output:** estimated VO2 max
- **Use Case:** Tracking fitness improvements over time

### 4. Calorie Burn Calculator
**Priority: Medium**
- Estimate calories burned during running
- Factors: weight, distance, pace, terrain
- **Input:** runner weight, distance, time/pace
- **Output:** estimated calories burned
- **Use Case:** Training log and nutrition planning

### 5. Split Time Calculator
**Priority: Medium**
- Calculate required split times for target race finish
- Even splits vs negative splits strategies
- **Input:** target finish time, race distance, split distance
- **Output:** required split times
- **Use Case:** Race pacing strategy planning

### 6. Pace Adjustments for Environmental Factors
**Priority: Low**
- Adjust paces/times for temperature, humidity, hills, and altitude.
- Based on research showing performance degradation in various conditions.
- **Input:** baseline pace, environmental data (temp, humidity, gradient, altitude)
- **Output:** adjusted pace recommendations
- **Use Case:** Adjusting training intensity for weather, terrain, and altitude.

### 7. Running Power Calculations
**Priority: Low**
- Calculate running power zones similar to cycling
- Estimate power output from pace and other factors
- **Input:** weight, pace, grade
- **Output:** estimated power output
- **Use Case:** Advanced training metrics for runners with power meters

### 8. Age-Graded Performance
**Priority: Medium**
- Calculate age-graded performance percentages
- Compare performances across different ages
- **Input:** age, gender, race time, distance
- **Output:** age-graded percentage and equivalent times
- **Use Case:** Fair comparison of performances across age groups

### 9. Training Load/TSS Calculator
**Priority: Low**
- Calculate Training Stress Score for runs
- Based on duration, intensity, and fitness level
- **Input:** duration, average HR or pace vs threshold
- **Output:** TSS value and training load
- **Use Case:** Managing training load and recovery

### 10. McMillan Running Calculator
**Priority: High**
- Predict race time equivalences.
- Provide training pace recommendations based on McMillan's methodology.
- **Input:** current race distance and time
- **Output:** predicted times for other distances, training paces.
- **Use Case:** Race planning and setting training paces.

### 11. Tinman (Tom Schwartz) Formulas
**Priority: Medium**
- Calculate training paces based on Critical Velocity.
- Offer an alternative to Daniels' and McMillan's training zones.
- **Input:** recent race performance
- **Output:** training paces (Easy, Marathon, CV, etc.)
- **Use Case:** Alternative training pace guidance.

### 12. Treadmill Pace and Incline Conversions
**Priority: Low**
- Convert treadmill paces to equivalent outdoor running paces.
- Calculate the effect of treadmill incline on effort and equivalent flat-ground pace.
- **Input:** Treadmill speed, treadmill incline (%)
- **Output:** Equivalent flat-ground pace (e.g., "min/km" or "min/mile")
- **Use Case:** Accurately translate treadmill workouts to outdoor conditions.

### 13. Race Fueling & Hydration Calculator
**Priority: Low**
- Estimate carbohydrate and fluid needs for endurance races.
- **Input:** Race distance or expected duration, runner's body weight.
- **Output:** Recommended grams of carbohydrates per hour and fluid volume per hour.
- **Use Case:** Help runners develop a fueling and hydration strategy to avoid bonking.

### 14. Basic Training Plan Generator
**Priority: Low**
- Generate a high-level, week-by-week training structure based on a goal race.
- **Input:** Goal race distance, current fitness level (VDOT), weeks to train, days per week.
- **Output:** A structured weekly schedule with mileage and key workouts (Long Run, Tempo, etc.) with target paces from the `training_paces` tool.
- **Use Case:** Provide runners with a structured, personalized plan to prepare for a race.

## Implementation Notes

### Recommended Implementation Order
1. **McMillan Running Calculator** (High priority, core feature)
2. **Tinman (Tom Schwartz) Formulas** (Provides an alternative training philosophy)
3. **VO2 Max Estimation** (Natural extension of existing VDOT work)
4. **Age-Graded Performance** (Popular and high-value feature)
5. **Split Time Calculator** (Practical tool for race prep)
6. **Heart Rate Zones** (Karvonen, etc. - another core training tool)
7. **Calorie Burn Calculator** (General fitness appeal)
8. The remaining low-priority items, with the **Basic Training Plan Generator** last due to its complexity.

### Technical Considerations
- Maintain consistency with existing API patterns
- Ensure all calculations include proper error handling
- Consider adding unit tests for each new calculation
- Document formulas and sources for transparency
- Consider configuration options for different calculation methodologies

### Implementation Notes: Basic Training Plan Generator

#### Architectural Consideration: Plan Generation Logic
When implementing the `Basic Training Plan Generator`, the core logic for constructing the plan would reside within the MCP server tool, not within the LLM.

-   **Server-Side Logic**:
    -   **Pros**: Reliable, consistent, and safe plans. Output is structured (JSON), and the logic is maintainable and testable.
    -   **Cons**: More rigid; requires more upfront development to codify training rules.

-   **LLM-Side Logic**:
    -   **Pros**: More flexible and can handle conversational nuance.
    -   **Cons**: Higher risk of unreliable, inconsistent, or unsafe plans. Output is unstructured, and the process is inefficient.

**Conclusion**: For a feature where safety and reliability are critical, a dedicated, deterministic tool in the server is perhaps the better architectural choice. The LLM should be used to understand the user's request and call the tool. The LLM could subsequently adjust the baseline retrieved from the tool based on user preferences and trainign progress.

**Alternative Hybrid Approach**: Have the MCP server provide the LLM with a rather prescriptive prompt to generate a plan based on proven methodologies (the same we would use if implementing the plan generation entirely inside MCP server). That way the MCP would more or less guide the LLM but the actual plan generation would happen inside the LLM.

#### High-level Implementation Plan for Server-side Plan Generation
The following outlines a high-level approach for implementing the `Basic Training Plan Generator`:

1.  **Research and Data Gathering**:
    -   Perform web searches to gather information on common training plan structures for various race distances (5k, 10k, half marathon, marathon).
    -   Focus on reputable sources (e.g., Jack Daniels, Hal Higdon) to understand typical training cycles, key workout types (Long Run, Tempo, Intervals), progression rules (e.g., 10% rule), and tapering strategies.

2.  **Defining the Core Logic and Structure**:
    -   **Location**: Create a new module at `src/running_formulas_mcp/generators/training_plan.py`.
    -   **Inputs**: The tool will take `goal_distance`, `current_fitness` (as a VDOT score), `weeks_to_race`, and `days_per_week` as input.
    -   **Templates**: Define base templates for each race distance, outlining the structure of a typical training week (e.g., `[Long Run, Tempo, Easy, Rest, ...]`).
    -   **Progression**: Implement logic to scale weekly mileage and workout intensity based on the user's fitness and the number of weeks to the race. This includes building volume and a final tapering period.
    -   **Pace Integration**: Leverage the existing `calculate_vdot` and `training_paces` tools to determine the user's fitness level and provide specific target paces for each workout in the plan.

3.  **Generating the Output**:
    -   **Format**: The final output will be a structured JSON object.
    -   **Structure**: The object will contain a list of "week" objects, each detailing the `week_number`, `total_mileage`, and a list of `workout` objects for that week. Each workout will specify the `day`, `type`, `distance`, and `target_pace`.

### Data Sources and References
- [Daniels' Running Formula](https://www.goodreads.com/book/show/161692.Daniels_Running_Formula)
- [Age-grading tables from World Masters Athletics](https://world-masters-athletics.org/)
- [ACSM guidelines for exercise physiology](https://www.acsm.org/education-resources/books/guidelines-for-exercise-testing-and-prescription)
- [Published research on environmental effects on performance](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC3763322/)
- [McMillan Running Calculator](https://www.mcmillanrunning.com/)
- [Tinman Endurance Coaching](https://tinmancoach.com/)
- [The Karvonen Formula](https://www.bcmj.org/articles/endurance-exercise-prescription-karvonen-formula)

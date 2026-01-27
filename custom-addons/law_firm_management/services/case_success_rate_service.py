from ..repositories.case_repository import CaseRepository
from ..repositories.lawyer_repository import LawyerRepository

class BaseSuccessRateStrategy:
    """
    Base interface for all success rate strategies.
    Intentionally minimal to support diverse implementation approaches:
    - Score/factor-based (rule-based calculations)
    - ML-based (machine learning models)
    - External service-based (API calls)
    - Hybrid approaches
    """
    def __init__(self, env, config=None):
        self.env = env
        self.config = config or {}

    def compute(self, case):
        """
        Compute success rate for a given case.

        :param case: law.case record
        :return: float between 0.0 and 100.0
        """
        raise NotImplementedError("Subclasses must implement compute()")


class ScoreBasedSuccessRateStrategy(BaseSuccessRateStrategy):
    """
    Intermediate abstract class for strategies that use weighted score/factors pattern.
    Provides common helper methods for calculating lawyer performance, evidence scores, etc.
    """

    def __init__(self, env, config=None):
        super().__init__(env, config)
        self.case_repo = CaseRepository(env)
        self.lawyer_repo = LawyerRepository(env)

    def _compute_lawyer_score(self, case):
        """
        Calculate lawyer's contribution to success rate based on experience and track record.
        """
        lawyer_score = 50.0

        lawyer = case.responsible_employee_id
        if not lawyer:
            return lawyer_score

        # Experience bonus: up to 20 points
        experienced_bonus = min((lawyer.years_of_experience or 0) * 2, 20)
        lawyer_score += experienced_bonus

        # Historical win rate in this practice area
        if case.practice_area_id:
            # Use repository to find past cases for this lawyer
            past_cases = self.case_repo.find_all([
                ('responsible_employee_id', '=', lawyer.id),
                ('practice_area_id', '=', case.practice_area_id.id),
                ('state', '=', 'closed'),
                ('case_outcome', 'in', ['won', 'lost']),
            ])
            total_past = len(past_cases)

            if total_past:
                wins = len(past_cases.filtered(lambda p: p.case_outcome == 'won'))
                win_rate = (wins / total_past) * 100

                if win_rate >= 75:
                    lawyer_score += 15
                elif win_rate >= 50:
                    lawyer_score += 5
                elif win_rate < 30:
                    lawyer_score -= 10
                else:
                    lawyer_score -= 5

        # Workload penalty: too many active cases reduces effectiveness
        # Use repository to count active cases
        active_cases = self.case_repo.count([
            ('responsible_employee_id', '=', lawyer.id),
            ('state', '=', 'open'),
            ('id', '!=', case.id),
        ])
        if active_cases > 5:
            lawyer_score -= 15

        return max(0.0, min(100.0, lawyer_score))

    def _compute_evidence_score(self, case, score_map=None):
        """
        Calculate evidence strength contribution.
        """
        if score_map is None:
            score_map = {
                'weak': 10,
                'moderate': 40,
                'strong': 70,
                'conclusive': 90
            }

        if case.evidence_strength:
            return score_map.get(case.evidence_strength, 0)
        return 0

    def _compute_strength_score(self, case, score_map=None):
        """
        Calculate case strength contribution.
        """
        if score_map is None:
            score_map = {
                'very_weak': 10,
                'weak': 30,
                'moderate': 50,
                'strong': 75,
                'very_strong': 95
            }

        if case.case_strength:
            return score_map.get(case.case_strength, 0)
        return 0

    def _compute_precedent_score(self, case, weight=1.0):
        """
        Calculate precedent analysis contribution.
        """
        if case.client_role and case.precedent_count:
            precedent_ratio = (case.favorable_precedents_count / case.precedent_count) * 100
            return precedent_ratio * weight
        return 0


class DefaultSuccessRateStrategy(ScoreBasedSuccessRateStrategy):
    """
    Default success rate calculation using balanced weights across all factors.
    """
    def compute(self, case):
        score = 0.0
        factors = 0

        # Evidence strength
        evidence_score = self._compute_evidence_score(case)
        if evidence_score:
            score += evidence_score
            factors += 1

        # Case strength
        strength_score = self._compute_strength_score(case)
        if strength_score:
            score += strength_score
            factors += 1

        # Precedent analysis
        precedent_score = self._compute_precedent_score(case)
        if precedent_score:
            score += precedent_score
            factors += 1

        avg_score = (score / factors) if factors else 0.0
        lawyer_score = self._compute_lawyer_score(case)

        # Default weights: 70% case factors, 30% lawyer performance
        final_rate = (avg_score * 0.7) + (lawyer_score * 0.3)

        return max(0.0, min(100.0, final_rate))


class CivilSuccessRateStrategy(ScoreBasedSuccessRateStrategy):
    """
    Civil law success rate calculation.
    Emphasizes lawyer expertise more heavily (40%) due to negotiation importance.
    """
    def compute(self, case):
        score = 0.0
        factors = 0

        # Use inherited helper methods
        evidence_score = self._compute_evidence_score(case)
        if evidence_score:
            score += evidence_score
            factors += 1

        strength_score = self._compute_strength_score(case)
        if strength_score:
            score += strength_score
            factors += 1

        precedent_score = self._compute_precedent_score(case)
        if precedent_score:
            score += precedent_score
            factors += 1

        avg_score = (score / factors) if factors else 0.0
        lawyer_score = self._compute_lawyer_score(case)

        # Civil law weights: 60% case factors, 40% lawyer expertise
        final_score = (avg_score * 0.6) + (lawyer_score * 0.4)
        return max(0.0, min(100.0, final_score))


class PenalSuccessRateStrategy(ScoreBasedSuccessRateStrategy):
    """
    Emphasizes evidence quality (75%) with custom scoring that reflects criminal law standards.
    """
    def compute(self, case):
        score = 0.0
        factors = 0

        # Criminal law emphasizes evidence quality - custom scores
        evidence_scores = {
            'weak': 10,
            'moderate': 45,
            'strong': 80,
            'conclusive': 95
        }
        evidence_score = self._compute_evidence_score(case, score_map=evidence_scores)
        if evidence_score:
            score += evidence_score
            factors += 1

        # Criminal case strength has different thresholds
        strength_scores = {
            'very_weak': 10,
            'weak': 25,
            'moderate': 50,
            'strong': 70,
            'very_strong': 90
        }
        strength_score = self._compute_strength_score(case, score_map=strength_scores)
        if strength_score:
            score += strength_score
            factors += 1

        # Precedents weigh less in criminal law (60% weight)
        precedent_score = self._compute_precedent_score(case, weight=0.6)
        if precedent_score:
            score += precedent_score
            factors += 1

        avg_score = (score / factors) if factors else 0.0
        lawyer_score = self._compute_lawyer_score(case)

        # Criminal law weights: 75% case factors, 25% lawyer expertise
        final_rate = (avg_score * 0.75) + (lawyer_score * 0.25)
        return max(0.0, min(100.0, final_rate))

# ===== Example: Non-Score-Based Strategies =====

class MLBasedSuccessRateStrategy(BaseSuccessRateStrategy):
    """
    Example ML-based strategy that could use a trained model.
    Demonstrates flexibility - no score/factors required.
    """
    def compute(self, case):
        """
        In a real implementation, this would:
        1. Extract features from the case
        2. Load a trained ML model (from config or file)
        3. Make predictions
        4. Return the predicted success rate
        """
        # Placeholder implementation - returns a default value
        # In production, you'd integrate with sklearn, tensorflow, etc.

        # Example: could use config to specify model path
        # model_path = self.config.get('model_path', '/path/to/model.pkl')
        # model = load_model(model_path)
        # features = self._extract_features(case)
        # return model.predict(features)[0]

        return 50.0  # Placeholder

    def _extract_features(self, case):
        """Extract numerical features for ML model."""
        # Example feature extraction
        features = {
            'lawyer_experience': case.responsible_employee_id.years_of_experience or 0,
            'precedent_ratio': (case.favorable_precedents_count / max(case.precedent_count, 1)),
            'evidence_encoded': {'weak': 0, 'moderate': 1, 'strong': 2, 'conclusive': 3}.get(
                case.evidence_strength, 0
            ),
            # ... more features
        }
        return features

class ExternalServiceSuccessRateStrategy(BaseSuccessRateStrategy):
    """
    Example external API-based strategy.
    Demonstrates how to integrate with third-party services.
    """
    def compute(self, case):
        """
        In a real implementation, this would:
        1. Prepare request payload from case data
        2. Call external API (using config for credentials)
        3. Parse and return the response
        """
        # Placeholder implementation
        # In production:
        # api_url = self.config.get('api_url', 'https://api.example.com/predict')
        # api_key = self.config.get('api_key')
        #
        # import requests
        # payload = self._prepare_payload(case)
        # response = requests.post(
        #     api_url,
        #     json=payload,
        #     headers={'Authorization': f'Bearer {api_key}'}
        # )
        # return response.json()['success_rate']

        return 50.0  # Placeholder

    def _prepare_payload(self, case):
        """Prepare API request payload from case data."""
        return {
            'case_type': case.practice_area_id.code if case.practice_area_id else None,
            'evidence_strength': case.evidence_strength,
            'lawyer_experience': case.responsible_employee_id.years_of_experience or 0,
            # ... more fields
        }

class StrategyRegistry:
    _REGISTRY = {
        'CIV': CivilSuccessRateStrategy,
        'civil': CivilSuccessRateStrategy,
        'PEN': PenalSuccessRateStrategy,
        'penal': PenalSuccessRateStrategy,
    }

    @classmethod
    def get_strategy(cls, practice_area_code):
        """
        Get strategy class for a practice area code.
        Falls back to DefaultSuccessRateStrategy if no specific strategy found.

        :param practice_area_code: Practice area code (e.g., 'CIV', 'PEN')
        :return: Strategy class
        """
        if not practice_area_code:
            return DefaultSuccessRateStrategy

        # Try exact match first, then try lowercase
        strategy_cls = cls._REGISTRY.get(practice_area_code)
        if not strategy_cls and isinstance(practice_area_code, str):
            strategy_cls = cls._REGISTRY.get(practice_area_code.lower())

        return strategy_cls or DefaultSuccessRateStrategy

    @classmethod
    def register_strategy(cls, code, strategy_class):
        """
        Dynamically register a new strategy at runtime.
        Useful for plugins or custom extensions.

        :param code: Practice area code
        :param strategy_class: Strategy class (must inherit from BaseSuccessRateStrategy)
        """
        if not issubclass(strategy_class, BaseSuccessRateStrategy):
            raise ValueError(f"{strategy_class} must inherit from BaseSuccessRateStrategy")
        cls._REGISTRY[code] = strategy_class


class CaseSuccessRateService:
    """
    Service for computing case success rates using the Strategy pattern.
    Delegates computation to appropriate strategy based on practice area.
    """
    def __init__(self, env, config=None):
        self.env = env
        self.config = config or {}

    def compute(self, case):
        """
        Compute success rate for a case using the appropriate strategy.

        :param case: law.case record
        :return: float between 0.0 and 100.0
        """
        practice_area_code = None
        if case.practice_area_id:
            practice_area_code = getattr(case.practice_area_id, 'code', None) or \
                                getattr(case.practice_area_id, 'name', None)

        strategy_cls = StrategyRegistry.get_strategy(practice_area_code)
        strategy = strategy_cls(self.env, config=self.config)

        return strategy.compute(case)

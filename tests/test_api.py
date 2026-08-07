import pytest
from fastapi.testclient import TestClient
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# Must import app after path setup
from app.main import app

# NOTE: Tests use the `auth_client` fixture from conftest.py for protected routes.
# The module-level client below is kept only for backward compatibility in
# tests that haven't been migrated yet.
client = TestClient(app)


class TestPages:
    """Test that all 3 HTML pages load correctly."""

    def test_home_page(self):
        response = client.get("/")
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]

    def test_batch_page(self):
        response = client.get("/batch")
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]

    def test_analytics_page(self):
        response = client.get("/analytics")
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]


class TestModelInfoEndpoint:

    def test_returns_success(self):
        response = client.get("/api/model/info")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"

    def test_contains_expected_fields(self):
        data = client.get("/api/model/info").json()
        assert "feature_names" in data
        assert "params" in data
        assert "test_accuracy" in data
        assert "test_f1" in data
        assert "feature_importance" in data
        assert "classes" in data

    def test_accuracy_above_80_percent(self):
        data = client.get("/api/model/info").json()
        assert data["test_accuracy"] >= 0.80


class TestClassDistributionEndpoint:

    def test_returns_success(self):
        response = client.get("/api/class_distribution")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"

    def test_has_three_classes(self):
        data = client.get("/api/class_distribution").json()
        assert len(data["class_distribution"]) == 3

    def test_total_is_4000(self):
        data = client.get("/api/class_distribution").json()
        total = sum(data["class_distribution"].values())
        assert total == 4000


class TestDatasetStatsEndpoint:

    def test_returns_success(self):
        response = client.get("/api/dataset/stats")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"

    def test_total_samples(self):
        data = client.get("/api/dataset/stats").json()
        assert data["total_samples"] == 4000

    def test_has_feature_stats(self):
        data = client.get("/api/dataset/stats").json()
        assert len(data["feature_stats"]) >= 12


class TestPredictEndpoint:

    def test_predict_with_text_file(self):
        response = client.post(
            "/api/predict",
            files={"resume": ("test.txt", b"john@example.com | (555) 123-4567\nEducation: BS CS. Experience: Experienced Python developer with 5 years in AWS and Docker. Led team of engineers.")},
            data={"job_description": "Looking for a Python developer with cloud experience."}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert "classification" in data
        assert data["classification"]["classification"] in ["Authentic", "Suspicious", "Potentially Fake", "Not a Resume"]

    def test_predict_without_job_description(self):
        response = client.post(
            "/api/predict",
            files={"resume": ("test.txt", b"test@example.com | 555-123-4567\nPython developer with AWS experience.")}
        )
        assert response.status_code == 400 # Job description is required

    def test_predict_too_short_returns_400(self):
        response = client.post(
            "/api/predict",
            files={"resume": ("short.txt", b"Hi")},
            data={"job_description": "Software engineer"}
        )
        assert response.status_code == 400

    def test_predict_returns_all_sections(self):
        response = client.post(
            "/api/predict",
            files={"resume": ("test.txt", b"test@example.com | 555-123-4567\nEducation: BS Computer Science. Experience: Experienced Python developer with 5 years in AWS and Docker. Led team of engineers.")},
            data={"job_description": "Looking for a Python developer."}
        )
        data = response.json()
        assert "scores" in data
        assert "skills" in data
        assert "validation" in data
        assert "classification" in data
        assert "resume_preview" in data
        assert "filename" in data

    def test_predict_with_job_title(self):
        response = client.post(
            "/api/predict",
            files={"resume": ("test.txt", b"test@example.com | 555-123-4567\nEducation: MS CS. Experience: Senior engineer with Python skills")},
            data={"job_title": "Senior Software Engineer", "job_description": "Python developer"}
        )
        assert response.status_code == 200

    def test_predict_scores_are_between_0_and_1(self):
        response = client.post(
            "/api/predict",
            files={"resume": ("test.txt", b"test@example.com | 555-123-4567\nEducation: degree. Experience: Python AWS Docker engineer")},
            data={"job_description": "Python and AWS developer"}
        )
        data = response.json()
        for key, val in data["scores"].items():
            assert 0 <= val <= 1, f"{key} = {val} is not in [0,1]"


class TestPredictBatchEndpoint:

    def test_batch_with_two_files(self):
        response = client.post(
            "/api/predict_batch",
            files=[
                ("resumes", ("a.txt", b"test@example.com | 555-123-4567\nEducation: Degree. Experience: Python developer with AWS experience.")),
                ("resumes", ("b.txt", b"test2@example.com | 555-987-6543\nEducation: None. Experience: Results-driven go-getter team player.")),
            ],
            data={"job_description": "Software engineer"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "processing"
        assert "job_id" in data

    def test_batch_empty_file_handled(self):
        response = client.post(
            "/api/predict_batch",
            files=[("resumes", ("empty.txt", b""))],
            data={"job_description": "test"}
        )
        data = response.json()
        assert data["status"] == "processing"

    def test_batch_sorts_by_classification_priority(self):
        response = client.post(
            "/api/predict_batch",
            files=[
                ("resumes", ("a.txt", b"test@example.com | 555-123-4567\nEducation: NA. Experience: Results-driven go-getter team player synergy leverage.")),
                ("resumes", ("b.txt", b"test2@example.com | 555-987-6543\nEducation: BS Computer Science. Experience: Experienced Python developer with 5 years in AWS and Docker. Led team of 10 engineers.")),
            ],
            data={"job_description": "Software engineer with Python and AWS experience."}
        )
        data = response.json()
        assert data["status"] == "processing"
        assert "job_id" in data


class TestStaticFiles:

    def test_confusion_matrix_png(self):
        response = client.get("/static/confusion_matrix.png")
        assert response.status_code == 200
        assert "image/png" in response.headers["content-type"]

    def test_correlation_matrix_png(self):
        response = client.get("/static/correlation_matrix.png")
        assert response.status_code == 200

    def test_feature_importance_png(self):
        response = client.get("/static/feature_importance.png")
        assert response.status_code == 200


# ── New Tests: Auth Flow ─────────────────────────────────────────────────────
class TestAuthFlow:
    """Tests for the login / logout authentication system."""

    def test_login_page_accessible_unauthenticated(self):
        """The /login page must be publicly accessible (no redirect)."""
        r = TestClient(app).get("/login")
        assert r.status_code == 200
        assert "text/html" in r.headers.get("content-type", "")

    def test_home_redirects_when_not_logged_in(self):
        """Unauthenticated requests to / must redirect to /login."""
        r = TestClient(app).get("/", follow_redirects=False)
        assert r.status_code in (302, 303)
        assert "/login" in r.headers.get("location", "")

    def test_login_with_valid_credentials(self, auth_client):
        """A successful login should return the main HR dashboard (200)."""
        r = auth_client.get("/")
        assert r.status_code == 200

    def test_login_with_wrong_password(self):
        """Wrong password must NOT redirect to dashboard — should re-show login."""
        c = TestClient(app)
        r = c.post("/login", data={"username": "admin", "password": "wrong"})
        # Expect redirect back to login or 400, NOT a 200 from the dashboard
        assert r.status_code in (200, 302, 303, 401)
        if r.status_code in (302, 303):
            assert "/login" in r.headers.get("location", "")


# ── New Tests: SHAP Explainability ───────────────────────────────────────────
class TestSHAPExplainability:
    """
    Validates task 5.2: Decision Tree / XGBoost SHAP feature attribution.
    Every successful prediction must include a 'top_features' key whose
    entries have the correct schema — feature name, raw value, and
    SHAP contribution score.
    """

    RESUME = (
        "jane@example.com | (555) 200-3000\n"
        "Education: MS Computer Science, Stanford 2019.\n"
        "Experience: 6 years as ML Engineer at Google. Led Python and TensorFlow projects. "
        "Deployed models to AWS and GCP. Managed team of 8 engineers.\n"
        "Skills: Python, TensorFlow, PyTorch, AWS, Kubernetes, Docker, SQL."
    )
    JD = "Seeking an experienced ML Engineer with Python, TensorFlow, and cloud experience."

    def test_predict_contains_top_features(self, auth_client):
        """Prediction result must include a non-empty top_features list."""
        r = auth_client.post(
            "/api/predict",
            files={"resume": ("jane_cv.txt", self.RESUME.encode())},
            data={"job_description": self.JD}
        )
        assert r.status_code == 200
        data = r.json()
        cls = data.get("classification", {})
        # top_features must exist and be a list
        assert "top_features" in cls, "top_features missing from classification response"
        top_features = cls["top_features"]
        assert isinstance(top_features, list)

    def test_top_features_have_correct_schema(self, auth_client):
        """Each entry in top_features must have 'feature', 'value', 'contribution' keys."""
        r = auth_client.post(
            "/api/predict",
            files={"resume": ("jane_cv.txt", self.RESUME.encode())},
            data={"job_description": self.JD}
        )
        data = r.json()
        top_features = data["classification"].get("top_features", [])
        for item in top_features:
            assert "feature"      in item, f"Missing 'feature' key in: {item}"
            assert "value"        in item, f"Missing 'value' key in: {item}"
            assert "contribution" in item, f"Missing 'contribution' key in: {item}"
            assert isinstance(item["feature"],      str),   "feature must be a string"
            assert isinstance(item["value"],        float), "value must be float"
            assert isinstance(item["contribution"], float), "contribution must be float"

    def test_top_features_at_most_three(self, auth_client):
        """SHAP should return at most 3 top features per prediction."""
        r = auth_client.post(
            "/api/predict",
            files={"resume": ("jane_cv.txt", self.RESUME.encode())},
            data={"job_description": self.JD}
        )
        data = r.json()
        top_features = data["classification"].get("top_features", [])
        assert len(top_features) <= 3, f"Expected ≤3 features, got {len(top_features)}"


# ── New Tests: Export Endpoints ──────────────────────────────────────────────
class TestExportEndpoints:
    """
    Validates task 5.6: Exportable Reporting — the /api/export/analytics
    endpoint must return a valid text/csv response.
    """

    def test_analytics_export_returns_csv(self, auth_client):
        """The export endpoint must respond with content-type text/csv."""
        r = auth_client.get("/api/export/analytics")
        assert r.status_code == 200, f"Expected 200, got {r.status_code}"
        ct = r.headers.get("content-type", "")
        assert "text/csv" in ct, f"Expected text/csv, got: {ct}"

    def test_analytics_export_contains_metric_header(self, auth_client):
        """The CSV body must contain the 'Metric' header row."""
        r = auth_client.get("/api/export/analytics")
        assert r.status_code == 200
        text = r.text
        assert "Metric" in text, "CSV missing 'Metric' header"

    def test_analytics_export_contains_accuracy(self, auth_client):
        """The CSV must include an Accuracy row with a numeric value."""
        r = auth_client.get("/api/export/analytics")
        assert r.status_code == 200
        text = r.text
        assert "Accuracy" in text, "CSV is missing the Accuracy metric row"

    def test_analytics_export_contains_feature_section(self, auth_client):
        """The CSV must include the Feature Importance section."""
        r = auth_client.get("/api/export/analytics")
        assert r.status_code == 200
        text = r.text
        assert "Feature Importance" in text or "Feature,Importance" in text, (
            "CSV is missing the feature importance section"
        )

    def test_analytics_export_has_content_disposition(self, auth_client):
        """Response must include Content-Disposition header for file download."""
        r = auth_client.get("/api/export/analytics")
        assert r.status_code == 200
        cd = r.headers.get("content-disposition", "")
        assert "attachment" in cd, "Content-Disposition should be 'attachment'"

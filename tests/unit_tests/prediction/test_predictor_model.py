import os

import pytest
from src.Classifier import Classifier, load_predictor_model, save_predictor_model
from src.preprocessing.pipeline import run_pipeline


@pytest.fixture
def classifier(sample_train_data, schema_provider):
    """Define the regressor fixture"""
    target = sample_train_data[schema_provider.target]
    sample_train_data = sample_train_data.drop(columns=[schema_provider.id, schema_provider.target])
    sample_train_data = run_pipeline(sample_train_data, schema_provider, training=True)
    sample_train_data[schema_provider.target] = target
    classifier = Classifier(sample_train_data, schema=schema_provider)
    return classifier


def test_fit_predict(classifier, sample_train_data, sample_test_data, schema_provider):
    """
    Test if the fit method trains the model correctly and if predict method work as expected.
    """
    classifier.train()
    sample_test_data = sample_test_data.drop(columns=[schema_provider.id, schema_provider.target])
    sample_test_data = run_pipeline(sample_test_data, schema_provider, training=False)
    predictions = classifier.predict(sample_test_data)
    assert predictions.shape[0] == sample_test_data.shape[0]


def test_classifier_str_representation(classifier):
    """
    Test the `__str__` method of the `Classifier` class.

    The test asserts that the string representation of a `Regressor` instance is
    correctly formatted and includes the model name and the correct hyperparameters.

    Args:
        classifier (Classifier): An instance of the `Classifier` class,
            created using the `hyperparameters` fixture.

    Raises:
        AssertionError: If the string representation of `classifier` does not
            match the expected format.
    """
    classifier_str = str(classifier)
    assert classifier.model_name in classifier_str


def test_save_predictor_model(tmpdir, classifier, sample_train_data, schema_provider):
    """
    Test that the 'save_predictor_model' function correctly saves a Model instance
    to disk.
    """
    classifier.train()
    model_dir_path = os.path.join(tmpdir, "model")
    save_predictor_model(classifier, model_dir_path)
    assert os.path.exists(model_dir_path)
    assert len(os.listdir(model_dir_path)) >= 1


def test_load_predictor_model(tmpdir, classifier, sample_train_data, schema_provider):
    """
    Test that the 'load_predictor_model' function correctly loads a Model
    instance from disk.
    """

    classifier.train()
    model_dir_path = os.path.join(tmpdir, "model")
    save_predictor_model(classifier, model_dir_path)
    loaded_clf = load_predictor_model(model_dir_path)
    assert isinstance(loaded_clf, Classifier)

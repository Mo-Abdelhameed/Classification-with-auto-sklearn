import os
import re
import warnings
from typing import List
import numpy as np
import pandas as pd
from joblib import dump, load
from sklearn.exceptions import NotFittedError
from config import paths
from schema.data_schema import ClassificationSchema
from utils import read_json_as_dict
from autosklearn.classification import AutoSklearnClassifier
from autosklearn.metrics import f1_macro, f1

warnings.filterwarnings("ignore")
PREDICTOR_FILE_NAME = "predictor.joblib"


def clean_and_ensure_unique(names: List[str]) -> List[str]:
    """
    Clean the provided column names by removing special characters and ensure their
    uniqueness.

    The function first removes any non-alphanumeric character (except underscores)
    from the names. Then, it ensures the uniqueness of the cleaned names by appending
    a counter to any duplicates.

    Args:
        names (List[str]): A list of column names to be cleaned.

    Returns:
        List[str]: A list of cleaned column names with ensured uniqueness.

    Example:
        >>> clean_and_ensure_unique(['3P%', '3P', 'Name', 'Age%', 'Age'])
        ['3P', '3P_1', 'Name', 'Age', 'Age_1']
    """

    # First, clean the names
    cleaned_names = [re.sub("[^A-Za-z0-9_]+", "", name) for name in names]

    # Now ensure uniqueness
    seen = {}
    for i, name in enumerate(cleaned_names):
        original_name = name
        counter = 1
        while name in seen:
            name = original_name + "_" + str(counter)
            counter += 1
        seen[name] = True
        cleaned_names[i] = name

    return cleaned_names


class Classifier:
    """A wrapper class for the AutoKeras Classifier.

    This class provides a consistent interface that can be used with other
    regressor models.
    """

    def __init__(self,
                 train_input: pd.DataFrame,
                 schema: ClassificationSchema,
                 ):
        """Construct a new Regressor."""
        self._is_trained: bool = False
        self.x = train_input.drop(columns=[schema.target])
        self.y = train_input[schema.target]
        self.schema = schema
        self.model_name = "auto_sklearn_classifier"
        self.model_config = read_json_as_dict(paths.MODEL_CONFIG_FILE_PATH)
        metric = f1 if schema.model_category == "binary_classification" else f1_macro  
        self.automl = AutoSklearnClassifier(
            time_left_for_this_task=self.model_config["task_time"],
            per_run_time_limit=self.model_config["model_time"],
            metric=metric,
            include=self.model_config["include"],
            seed=self.model_config["seed_value"],
        )

    def __str__(self):
        return f"Model name: {self.model_name}"

    def train(self) -> None:
        """Train the model on the provided data"""
        self.automl.fit(self.x, self.y)
        self._is_trained = True


    def predict(self, inputs: pd.DataFrame) -> np.ndarray:
        """Predict labels for the given data.

        Args:
            inputs (pandas.DataFrame): The input data.

        Returns:
            np.ndarray: The output predictions.
        """
        return self.automl.predict(inputs)
    

    def predict_proba(self, inputs: pd.DataFrame) -> np.ndarray:
        """Predict labels for the given data.

        Args:
            inputs (pandas.DataFrame): The input data.

        Returns:
            np.ndarray: The output probabilities.
        """
        return self.automl.predict_proba(inputs)
    

    def save(self, model_dir_path: str) -> None:
        """Save the classifier to disk.

        Args:
            model_dir_path (str): Dir path to which to save the model.
        """

        if not self._is_trained:
            raise NotFittedError("Model is not fitted yet.")
        dump(self, os.path.join(model_dir_path, PREDICTOR_FILE_NAME))

    @classmethod
    def load(cls, model_dir_path: str) -> "Classifier":
        """Load the regressor from disk.

        Args:
            model_dir_path (str): Dir path to the saved model.
        Returns:
            Classifier: A new instance of the loaded regressor.
        """
        return load(os.path.join(model_dir_path, PREDICTOR_FILE_NAME))
    

def predict_with_model(model: "Classifier", data: pd.DataFrame, return_proba: bool = False) -> np.ndarray:
    """
    Predict labels for the given data.

    Args:
        model (Classifier): The regressor model.
        data (pd.DataFrame): The input data.

    Returns:
        np.ndarray: The predicted labels.
    """
    return model.predict_proba(data) if return_proba else model.predict(data)


def save_predictor_model(model: "Classifier", predictor_dir_path: str) -> None:
    """
    Save the regressor model to disk.

    Args:
        model (Classifier): The regressor model to save.
        predictor_dir_path (str): Dir path to which to save the model.
    """
    if not os.path.exists(predictor_dir_path):
        os.makedirs(predictor_dir_path)
    model.save(predictor_dir_path)


def load_predictor_model(predictor_dir_path: str) -> "Classifier":
    """
    Load the regressor model from disk.

    Args:
        predictor_dir_path (str): Dir path where model is saved.

    Returns:
        Classifier: A new instance of the loaded regressor model.
    """
    return Classifier.load(predictor_dir_path)
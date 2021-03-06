# models
from attrdict import AttrDict
import numpy as np
import pandas as pd
from collections import Counter

import lightgbm as lgb
import xgboost as xgb
import catboost as ctb

from sklearn.base import BaseEstimator, ClassifierMixin

from keras import backend as K
from keras.models import Sequential
from keras.layers import Dense, Activation, BatchNormalization, Dropout
from keras.regularizers import l1_l2
from keras.optimizers import Adam, SGD

from lightgbm import LGBMClassifier
from sklearn.feature_selection import RFECV
from sklearn.model_selection import StratifiedKFold
from sklearn.metrics import roc_auc_score
from sklearn.cluster import KMeans
from sklearn.preprocessing import normalize

from ngboost import NGBClassifier
from sklearn.utils.multiclass import unique_labels
from imblearn.over_sampling import SMOTE

from ..common.utils import get_logger
import gc
gc.enable()

logger = get_logger()


class SklearnClassifier(BaseEstimator, ClassifierMixin):
  def __init__(self, classifier, **fit_params):
    logger.info('Inital Sklearn classifier...')
    self.params_ = fit_params
    self.classifier_ = classifier
    self.classes_ = np.array([0,1])

  def fit(self, X, y, *args, **kwargs):
    logger.info(f'Sklearn Classifier, fit.')
    logger.info(f'Sklearn Classifier, Training data shape: {X.shape}')
    logger.info(f'Sklearn Classifier, Training label shape: {y.shape}')
    self.estimator_ = self.classifier_(**self.params_) 
    self.estimator_.fit(X, y)
    logger.info(f'Sklearn Classifier, fit done.')
    return self

  def transform(self, X, *args, **kwargs):
    logger.info(f'Sklearn Classifier, transform.')
    logger.info(f'Sklearn Classifier, Training data shape: {X.shape}')
    pred = self.estimator_.predict_proba(X)[:, 1].reshape(-1)
    logger.info(f'Sklearn Classifier, transform done.')
    return pred
  
  def predict_proba(self, X, *args, **kwargs):
    logger.info(f'Sklearn Classifier, predict_proba')
    logger.info(f'Sklearn Classifier, Training data shape: {X.shape}')
    pred = self.estimator_.predict_proba(X)
    logger.info(f'Sklearn Classifier, predict_proba, done.')
    return pred    
  
  def get_params(self, deep=True):
    total_params = {'classifier': self.classifier_}
    total_params.update(self.params_)
    return total_params  
  def score(self, X, y, *args, **kwargs):
    return roc_auc_score(y, self.transform(X)) 


class LightGBM(BaseEstimator, ClassifierMixin):

  def __init__(self, **params):
    super().__init__()
    logger.info('initializing LightGBM ...')
    self.params_ = params
    # self.training_params_ = ['number_boosting_rounds','early_stopping_rounds']
    self.evaluation_function_ = None
    self.classes_ = np.array([0,1])
  
  def get_params(self, deep=True):
    return self.params_
  
  def fit(self, X, y, *args, **kwargs):
    logger.info('LightGBM, fit.')
    # evaluation_results = {}
    
    self._check_target_shape_and_type(y, 'y')

    y = self._format_target(y)

    logger.info(f'LightGBM, Training data shape: {X.shape}')
    logger.info(f'LightGBM, Training label shape: {y.shape}')
    self.estimator_ = lgb.LGBMClassifier(
      **self.params_['init']
    )
    self.estimator_.fit(
      X, y,
      **self.params_['fit'],
      eval_set=[(X,y)],
      eval_names=['train'],
    )
    logger.info('LightGBM, done fit.') 
    return self
  
  def transform(self, X, *args, **kwargs):
    logger.info('LightGBM, transform.')
    logger.info(f'LightGBM, transform, testing shape: {X.shape}')
    pred = self.estimator_.predict_proba(X)[:, 1].reshape(-1)
    logger.info(f'LightGBM, transform, predictions shape: {pred.shape}')
    logger.info('LightGBM, done transform.')
    return pred
  
  def score(self, X, y, *args, **kwargs):
    return roc_auc_score(y, self.transform(X)) 

  def predict_proba(self, X, *args, **kwargs):
    logger.info('LightGBM, predict_proba.')
    logger.info(f'LightGBM, predict_proba, testing shape: {X.shape}')
    pred = self.estimator_.predict_proba(X)
    logger.info('LightGBM, predict_proba, done.')
    return pred

  def _check_target_shape_and_type(self, target, name):
    if not any([isinstance(target, obj_type) for obj_type in [pd.Series, np.ndarray, list]]):
      raise TypeError(
          f'"target" must be "numpy.ndarray" or "pandas.Series" or "list", got {type(target)} instead.'
      )
    try:
      assert len(target.shape) == 1, f'"{name}" must 1-D. It is {target.shape} instead.'
    except:
      print(f'Cannot determine the shape of {name}.\n\
      Type must be "numpy.ndarray" or "pandas.Series" or "list", got {type(target)} and {target.shape} instead.')
    
  def _format_target(self, target):
    if isinstance(target, pd.Series):
      return target.values
    elif isinstance(target, np.ndarray):
      return target
    elif isinstance(target, list):
      return np.array(target)
    else:
      raise TypeError(
          f'"target" must be "numpy.ndarray" or "pandas.Series" or "list", got {type(target)} instead.'
      )


class XGBoost(BaseEstimator, ClassifierMixin):

  def __init__(self, **params):
    logger.info('initializing XGBoost ...')
    self.params_ = params
    # self.training_params_ = ['num_boost_round', 'early_stopping_rounds']
    self.evaluation_function_ = None
    self.classes_ = np.array([0,1])
  
  def get_params(self, deep=True):
    return self.params_
  
  
  def fit(self, X, y, *args, **kwargs):
    logger.info('XGBoost, fit.')
    logger.info(f'XGBoost, Training data shape: {X.shape}')
    logger.info(f'XGBoost, Training label shape: {y.shape}')

    # train = xgb.DMatrix(X, 
    #                     label=y)

    # evaluation_results = {}
    self.estimator_ = xgb.XGBClassifier(
      **self.params_['init']
    )
    self.estimator_.fit(
      X, y,
      **self.params_['fit'],
      eval_set=[(X,y)],
      
    )

    logger.info('XGBoost, done fit.')
    return self
  
  def transform(self, X, *args, **kwargs):
    logger.info('XGBoost, transform.')
    logger.info(f'XGBoost, transform, testing shape: {X.shape}')
    pred = self.estimator_.predict_proba(X)[:,1].reshape(-1)
    logger.info(f'XGBoost, transform, predictions shape: {pred.shape}')
    logger.info('XGBoost, done transform.')
    return pred
  
  def score(self, X, y, *args, **kwargs):
    return roc_auc_score(y, self.transform(X)) 

  def predict_proba(self, X, *args, **kwargs):
    logger.info('XGBoost, predict_proba.')
    logger.info(f'XGBoost, predict_proba, testing shape: {X.shape}')
    pred = self.estimator_.predict_proba(X)
    logger.info('XGBoost, predict_proba, done.')
    return pred


class CatBoost(BaseEstimator, ClassifierMixin):

  def __init__(self, **params):
    logger.info('Initializing Catboost...')
    self.params_ = params
    self.classes_ = np.array([0,1])

  def get_params(self, deep=True):
    return self.params_
  
  def fit(self, X, y, *args, **kwargs):
    logger.info(f'CatBoost, fit') 
    logger.info(f'CatBoost, training data shape {X.shape}')
    logger.info(f'CatBoost, training label shape {y.shape}')

    self.estimator_ = ctb.CatBoostClassifier(**self.params_)
    self.estimator_.fit(X,
                       y,
                       eval_set=[(X, y)])
    logger.info(f'CatBoost, done fit') 
    return self
  
  def transform(self, X, *args, **kwargs):
    logger.info(f'CatBoost, transform') 
    logger.info(f'CatBoost, transform, testing shape: {X.shape}')
    pred = self.estimator_.predict_proba(X)[:,1].reshape(-1)
    logger.info(f'CatBoost, transform, predictions shape: {pred.shape}')
    logger.info(f'CatBoost, done transform') 
    return pred
  
  def score(self, X, y, *args, **kwargs):
    return roc_auc_score(y, self.transform(X)) 

  def predict_proba(self, X, *args, **kwargs):
    logger.info(f'CatBoost, predict_proba') 
    logger.info(f'CatBoost, predict_proba, testing shape: {X.shape}')
    pred = self.estimator_.predict_proba(X)
    logger.info(f'CatBoost, predict_proba, done')
    return pred 
  
class NeuralNetwork(BaseEstimator, ClassifierMixin):
  
  def __init__(self, architecture_config, training_config, callbacks_config):
    logger.info('initializing NeuralNetwork ...')
    self.architecture_config_ = architecture_config
    self.model_params_ = architecture_config['model_params']
    self.optimizer_params_ = architecture_config['optimizer_params']
    self.training_config_ = training_config
    self.callbacks_config_ = callbacks_config
    self.classes_ = np.array([0,1])

  def get_params(self, deep=True):
    return {'architecture_config': self.architecture_config_,
            'training_config': self.training_config_,
            'callbacks_config': self.callbacks_config_
            }
    
  def _build_optimizer(self, **kwargs):
    return Adam(**self.optimizer_params_)
  
  def _build_loss(self, **kwargs):
    return 'binary_crossentropy'
  
  def _build_model(self, input_shape, **kwargs):
    K.clear_session()
    model = Sequential()
    for layer in range(self.model_params_['layers']):
      config = {key: val[layer] for key, val in self.model_params_.items() if key != 'layers'}
      if layer == 0:
        model.add(Dense(config['neurons'],
                        kernel_regularizer=l1_l2(l1=float(config['l1']), l2=float(config['l2'])),
                        input_shape=input_shape
                        ))
      else:
        model.add(Dense(config['neurons'],
                        kernel_regularizer=l1_l2(l1=config['l1'], l2=config['l2'])
                        ))
      if config['batch_norm']:
        model.add(BatchNormalization())
      model.add(Activation(config['activation']))
      model.add(Dropout(config['dropout']))
    
    return model
  
  def _compile_model(self, input_shape):
    model = self._build_model(input_shape)
    optimizer = self._build_optimizer()
    loss = self._build_loss()
    model.compile(optimizer=optimizer, loss=loss)
    return model
  
  def fit(self, X, y, *args, **kwargs):
    logger.info(f'Neural network, fit') 
    logger.info(f'Neural network, training data shape {X.shape}')
    logger.info(f'Neural network, training label shape {y.shape}')

    self.model = self._compile_model(input_shape=(X.shape[1], ))
    
    self.model.fit(X,
                    y,
                    validation_data=(X, y),
                    verbose=1,
                    **self.training_config_)
    logger.info(f'Neural network, done fit') 
    return self
  
  def score(self, X, y, *args, **kwargs):
    return roc_auc_score(y, self.transform(X)) 

  def transform(self, X, *args, **kwargs):
    logger.info(f'Neural network, transform') 
    logger.info(f'Neural network, transform, testing shape: {X.shape}')
    pred = self.model.predict(X, verbose=1)
    pred = np.array([x[0] for x in pred]).reshape(-1)
    logger.info(f'Neural network, transform, predictions shape: {pred.shape}')
    logger.info(f'Neural network, done transform') 
    return pred
  
  def predict_proba(self, X, *args, **kwargs):
    logger.info(f'Neural network, predict_proba') 
    logger.info(f'Neural network, predict_proba, testing shape: {X.shape}')
    pred = self.model.predict(X, verbose=1)
    pred = np.hstack(np.zeros(pred.shape[0]).reshape(-1), pred).reshape(-1, 2)
    logger.info(f'Neural network, predict_proba, done') 
    return pred


class NGBoost(BaseEstimator, ClassifierMixin):
  def __init__(self, **params):
    logger.info('Initializing NGBoost...')
    self.params_ = params
    self.classes_ = np.array([0,1])

  def get_params(self, deep=True):
    return self.params_
  
  def _to_numpy(self, X):
    if isinstance(X, pd.DataFrame) or isinstance(X, pd.Series):
      try:
        return X.to_numpy()
      except:
        ValueError('There is error when converting to numpy')
    elif isinstance(X, np.ndarray):      
      return X
    else:
      ValueError('X must be pandas DataFrame, Series or numpy ndarray')
  
  def fit(self, X, y, *args, **kwargs):
    logger.info(f'NGBoost, fit') 
    logger.info(f'NGBoost, training data shape {X.shape}')
    logger.info(f'NGBoost, training label shape {y.shape}')
    
    X_np = self._to_numpy(X)
    y_np = self._to_numpy(y)
    y_np = y_np.astype(int)
    print(f'np.unique(y_np)')
    self.estimator_ = NGBClassifier(**self.params_)
    self.estimator_.fit(X_np, y_np)
    logger.info(f'NGBoost, done fit') 
    return self
  
  def transform(self, X, *args, **kwargs):
    logger.info(f'NGBoost, transform') 
    logger.info(f'NGBoost, transform, testing shape: {X.shape}')
    X_np = self._to_numpy(X)
    pred = self.estimator_.predict_proba(X_np)[:,1].reshape(-1)
    logger.info(f'NGBoost, transform, predictions shape: {pred.shape}')
    logger.info(f'NGBoost, done transform') 
    return pred
  
  def score(self, X, y, *args, **kwargs):
    return roc_auc_score(y, self.transform(X)) 
  
  def predict_proba(self, X, *args, **kwargs):
    logger.info(f'NGBoost, predict_proba') 
    logger.info(f'NGBoost, predict_proba, testing shape: {X.shape}')
    X_np = self._to_numpy(X)
    pred = self.estimator_.predict_proba(X_np)
    logger.info(f'NGBoost, predict_proba, done') 
    return pred

class Blending(BaseEstimator, ClassifierMixin):
  def __init__(self, base_models, meta_model, use_feature_in_secondary=False):
    logger.info('Initializing Blending...')
    self.base_models_ = base_models
    self.meta_model_ = meta_model
    self.use_feature_in_secondary_ = use_feature_in_secondary
    self.classes_ = np.array([0,1])

  def get_params(self, deep=True):
    return {
      'base_models':self.base_models_,
      'meta_model': self.meta_model_,
      'use_feature_in_secondary': self.use_feature_in_secondary_,
      }
  
  def fit(self, X, y, *args, **kwargs):
    logger.info(f'Blending, fit') 
    logger.info(f'Blending, training data shape {X.shape}')
    logger.info(f'Blending, training label shape {y.shape}')
    
    hold_out_prediction = np.zeros((X.shape[0], len(self.base_models_)))
    for i, base_model in enumerate(self.base_models_):
      base_model.fit(X, y)
      pred = base_model.predict_proba(X)
      hold_out_prediction[:, i] = pred[:, 1]
    hold_out_prediction = pd.DataFrame(hold_out_prediction)
    if self.use_feature_in_secondary_ == True:
      X_meta = pd.concat([X, hold_out_prediction], axis=1)
      self.meta_model_.fit(X_meta, y)
    else:
      self.meta_model_.fit(hold_out_prediction, y)
      
    return self
  
  def transform(self, X, *args, **kwargs):
    return self.predict_proba(X, *args, kwargs)[:, 1].reshape(-1)
  
  def score(self, X, y, *args, **kwargs):
    return roc_auc_score(y, self.transform(X)) 
  
  def predict_proba(self, X, *args, **kwargs):
    logger.info(f'Blending, predict_proba') 
    logger.info(f'Blending, predict_proba, testing shape: {X.shape}')
    meta_feas = np.column_stack((
      model.predict_proba(X)[:, 1].reshape(-1) for model in self.base_models_
    ))
    print(f'Blending, predict_proba, meta_feas shape: {meta_feas.shape}')
    meta_feas = pd.DataFrame(meta_feas)

    if self.use_feature_in_secondary_ == True:
      X_meta = pd.concat([X, meta_feas], axis=1)
      pred = self.meta_model_.predict_proba(X_meta)
    else:
      pred = self.meta_model_.predict_proba(meta_feas)
    logger.info(f'Blending, predict_proba, predictions shape: {pred.shape}')
    logger.info(f'Blending, done predict_proba') 
    return pred

class FeatureSelection(BaseEstimator, ClassifierMixin):

  def __init__(self):
    logger.info('Initial FeatureSelection...')
  
  def fit(self, X, y, X_test, *arg, **kwargs):
    logger.info('FeatureSelection, fit')
    logger.info(f'FeatureSelection, fit, data train shape: {X.shape}')
    logger.info(f'FeatureSelection, fit, data test shape: {X_test.shape}')
    logger.info(f'FeatureSelection, fit, label shape: {y.shape}')

    logger.info('FeatureSelection, RFECV')
    estimator_ = LGBMClassifier(learning_rate=0.1,num_leaves=15,n_estimators=10,ranstdom_state=42)
    self.rfecv_ = RFECV(estimator=estimator_, step=1, cv=5, scoring='roc_auc')
    self.rfecv_.fit(X, y)

    logger.info('FeatureSelection, CovariateShift')
    self.covariateshift_ = CovariateShift()
    self.covariateshift_.fit(X, X_test)

    # logger.info('FeatureSelection, Correlation')
    # self.corr_ = DropCorrelation()
    # self.corr_.fit(X)

    logger.info('FeatureSelection, done fit')
    return self
  
  def transform(self, X, *args, **kwargs):
    logger.info('FeatureSelection, transform')

    rfecv_feas = set(X.columns[self.rfecv_.support_])
    covashift_feas = set(self.covariateshift_.transform(X))   
    # corr_feas = set(self.corr_.transform(X))

    logger.info('FeatureSelection, done transform')
    return list(rfecv_feas.intersection(covashift_feas))

class CovariateShift(BaseEstimator, ClassifierMixin):
  
  def __init__(self):
    logger.info('Initial CovariateShift...')

  def fit(self, X, X_test, *arg, **kwargs):
    logger.info('CovariateShift, fit')
    logger.info(f'CovariateShift, data shape: {X.shape}')
    logger.info(f'CovariateShift, data test shape: {X_test.shape}')
    X_temp = X.copy()
    X_temp['is_train'] = 1
    X_test_temp = X_test.copy()
    X_test_temp['is_train'] = 0
    
    df_combine = pd.concat([X_temp, X_test_temp], axis=0, ignore_index=True)
    y = df_combine['is_train']
    df_combine.drop(columns=['is_train'], inplace=True)
    self.estimator_ = LGBMClassifier(learning_rate=0.1,num_leaves=15,n_estimators=10,ranstdom_state=42)
    self.estimator_.fit(df_combine, y)

    logger.info('CovariateShift, done fit')
    del X_temp, X_test_temp, df_combine
    gc.collect()
    return self

  def transform(self, X, *arg, **kwargs):
    logger.info('CovariateShift, transform')
    logger.info(f'CovariateShift, transform, data shape: {X.shape}')
    cols_selected = int(len(X.columns)*0.85)

    feature_imp = pd.concat([pd.DataFrame(self.estimator_.feature_importances_),
              pd.DataFrame(list(X.columns))],
              axis=1, ignore_index=True)
    feature_imp.columns = ['Value', 'Feature']
    feature_imp = feature_imp.sort_values(by='Value', ascending=True)

    logger.info('CovariateShift, done transform')
    return feature_imp['Feature'][:cols_selected]

class DropCorrelation(BaseEstimator, ClassifierMixin):
    
    def fit(self, X, *args, **kwargs):
        return self

    def transform(self, X, *args, **kawrgs):
        corr_matrix = X.corr().abs()
        upper = corr_matrix.where(np.triu(np.ones(corr_matrix.shape), k=1).astype(bool))
        to_selected = [col for col in corr_matrix.columns if any(upper[col] < 0.95)]
        
        return to_selected

    def fit_transform(self, X, *args, **kwargs):
        return self.fit(X).transform(X)

class SMOte(BaseEstimator, ClassifierMixin):
  def __init__(self, **params):
    logger.info('Initializing SMOTE...')
    self.params_ = params

  def get_params(self, deep=True):
    return self.params_

  def fit(self, X, y, *args, **kwargs):
    logger.info('SMOTE, fit.')
    logger.info(f'SMOTE, data shape: {X.shape}')
    logger.info(f'SMOTE, label shape: {y.shape}')

    self.sm_ = SMOTE(**self.params_)
    logger.info('SMOTE, done fit.')
    return self
  
  def transform(self, X, y, *args, **kwargs):
    logger.info('SMOTE, transform.')
    logger.info(f'SMOTE, data shape: {X.shape}')
    logger.info(f'SMOTE, label shape: {y.shape}')

    X_new, y_new = self.sm_.fit_resample(X, y)
    X_new = pd.DataFrame(X_new, columns=X.columns)

    logger.info(f'SMOTE, Resampled dataset shape: {Counter(y_new)}')
    logger.info('SMOTE, done transform.')
    return X_new, y_new

  def fit_transform(self, X, y, *args, **kwargs):
    return self.fit(X, y).transform(X, y)


class KMeansFeaturizer:
  """
  Transform numeric data into k-mean cluster membership

  This transformation run kmean on input data in convert each data point into the index of 
  the closest cluster. If target information is given, then it is scaled and included as input 
  of k-means in order to derive clusters that obey the classification as well as as group of similar point together
  """
  def __init__(self, k=100, target_scale=2.0, random_state=None):
    self.k_ = k
    self.target_scale_ = target_scale
    self.random_state_ = random_state
  
  def convert_to_numpy(self, X):
    if type(X) == pd.DataFrame:
      try:
        return X.to_numpy()
      except:
        ValueError('X must be pandas DataFrame or numpy ndarray')
    return X

  def fit(self, X, y=None, *args, **kwargs):
    """
    Run k-means on the input data and find centroids.
    """
    X = self.convert_to_numpy(X)
    if y is None:
      # No target information, just do plain k-means
      km_model = KMeans(n_clusters=self.k_, random_state=self.random_state_, n_init=20, **kwargs)

      km_model.fit(X)

      self.cluster_centers_ = km_model.cluster_centers_
      self.km_model_ = km_model
      return self

    # With target information
    data = np.hstack((X, y[:, np.newaxis]*self.target_scale_)) 

    km_model_pretrain = KMeans(n_clusters=self.k_, random_state=self.random_state_, n_init=20, **kwargs)
    km_model_pretrain.fit(data)

    km_model = KMeans(n_clusters=self.k_, init=km_model_pretrain.cluster_centers_[:,:-1], n_init=1, max_iter=1, random_state=self.random_state_, **kwargs)
    km_model.fit(X)
    self.cluster_centers_ = km_model.cluster_centers_
    self.km_model_ = km_model
    return self
  
  def transform(self, X, **kwargs):
    cluster = self.km_model_.transform(X)
    return cluster
  
  def fit_transform(self, X, y=None, **kwargs):
    return self.fit(X,y,**kwargs).transform(X)















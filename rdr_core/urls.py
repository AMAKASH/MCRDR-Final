from django.urls import path
from . import views

urlpatterns = [
    path("", views.IndexView.as_view(), name='index-page'),
    path("dataset", views.dataset_view, name='dataset-page'),
    path("dataset/testing", views.TestDatasetView.as_view(),
         name='dataset-test-page'),
    path("dataset/add_new_from_test", views.AddDataFromTestView.as_view(),
         name='dataset-test-page'),
    path("case/evaluate", views.EvaluateSingle.as_view(), name='evaluate-single'),
    path("cornerstones", views.cornerstones_view, name='cornerstone-page'),
    path("rules", views.rules_view, name='rules-page'),
    path("rules/add", views.AddRule.as_view(), name='add-rule'),
    path("rules/update_conclusion",
         views.update_conclusion_view, name='update_conclusion'),
    path("run-till-error", views.run_view, name='run-view'),
    path("reset", views.reset_view, name='reset-view'),
    path("test/eval/", views.EvalTest.as_view(
        http_method_names=['get', 'post']), name='eval-test'),
]

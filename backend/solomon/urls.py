from django.urls import path

from .views import audiences_list, categories_list, context_view, playbooks_list, resources_list, review_queue, topics_list

from .guidance_views import guidance_view

app_name = "solomon"

urlpatterns = [
    path("api/solomon/guidance/", guidance_view, name="solomon-guidance"),
    path("api/solomon/categories/", categories_list, name="solomon-categories"),
    path("api/solomon/topics/", topics_list, name="solomon-topics"),
    path("api/solomon/audiences/", audiences_list, name="solomon-audiences"),
    path("api/solomon/resources/", resources_list, name="solomon-resources"),
    path("api/solomon/playbooks/", playbooks_list, name="solomon-playbooks"),
    path("api/solomon/context/", context_view, name="solomon-context"),
    path("api/solomon/governance/review-queue/", review_queue, name="solomon-review-queue"),
]

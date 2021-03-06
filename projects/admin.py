#
# Copyright 2014, Martin Owens <doctormo@gmail.com>
#
# This file is part of the software inkscape-web, consisting of custom
# code for the Inkscape project's django-based website.
#
# inkscape-web is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# inkscape-web is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with inkscape-web.  If not, see <http://www.gnu.org/licenses/>.
#
"""Project administrative interface"""

from django.contrib.admin import ModelAdmin, TabularInline, site,

from .models import Worker, Deliverable, Project, ProjectType, Criteria, Task

class WorkerInline(TabularInline):
    model = Worker
    extra = 0

class DeliverableInline(TabularInline):
    model = Deliverable

class UpdateInline(StackedInline):
    raw_id_fields = ('creator',)
    model = Report
    extra = 1

class ProjectAdmin(ModelAdmin):
    list_display = ('title', 'manager', 'started')
    raw_id_fields = ('manager', 'reviewer', 'second')
    fieldsets = (
        (None, {
          'fields': ('title', 'project_type', 'banner', 'logo', 'is_fundable', 'is_approved', 'difficulty')
        }),
        ('Timing', {
          'classes': ('collapse',),
          'fields': ('duration', 'started', 'finished'),
        }),
        ('People', {
          'classes': ('collapse',),
          'fields': ('proposer', 'manager', 'reviewer', 'second')
        }),
        ('Criteria', {
          'fields': ('criteria',),
        }),
        ('Static Information', {
          'classes': ('collapse',),
          'fields': ('slug', 'created', 'edited'),
        }),
    )
    readonly_fields = ('proposer','slug','created','edited')
    filter_horizontal = ("criteria",)
    inlines = (DeliverableInline, UpdateInline, WorkerInline)

site.register(Project, ProjectAdmin)
site.register(ProjectType)
site.register(Criteria)

class TaskInline(TabularInline):
    model = Task
    extra = 3

class DeliverableAdmin(ModelAdmin):
    list_display = ('name', 'project', 'finished')
    inlines = (TaskInline,)

site.register(Deliverable, DeliverableAdmin)

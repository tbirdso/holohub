{%- set op_class = cookiecutter.operator_slug.split('_')|map('capitalize')|join('') -%}
# {{ cookiecutter.project_name }} Pipeline

A stub Holoscan application demonstrating end-to-end use of `{{ op_class }}`.
{% if cookiecutter.language == 'cpp' %}Both C++ and Python implementations are provided and can be launched via `./holohub run {{ cookiecutter.module_slug }}_pipeline [--language python]`.{% else %}A Python implementation is provided and can be launched via `./holohub run {{ cookiecutter.module_slug }}_pipeline`.{% endif %}

> [!WARNING]
> This application is a work in progress — pipeline topology and operator wiring are pending implementation.

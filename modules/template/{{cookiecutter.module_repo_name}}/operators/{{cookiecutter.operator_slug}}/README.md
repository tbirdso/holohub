{%- set op_class = cookiecutter.operator_slug.split('_')|map('capitalize')|join('') -%}
# {{ op_class }}

A stub Holoscan operator under the {% if cookiecutter.language == 'cpp' %}`holoscan::{{ cookiecutter.module_slug }}` (C++) / {% endif %}`holoscan.{{ cookiecutter.module_slug }}` (Python) namespace.

> [!WARNING]
> This operator is a work in progress — ports, parameters, and compute logic are pending implementation.

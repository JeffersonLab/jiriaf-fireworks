import re
from monty.serialization import loadfn, dumpfn

from __init__ import SITE_CONFIG_TEMPLATE


def replace_placeholders(template, config):
    """
    Replace placeholders in the template with values from the config.
    """
    # Handle single placeholders like {{nodes}}, {{constraint}}, etc.
    for key, value in config.items():
        if isinstance(value, str) or isinstance(value, int):
            template = re.sub(f"{{{{{key}}}}}", str(value), template)

    # Handle lists for vkubelet_pod_ips and custom_metrics_ports
    template = replace_list_placeholder(template, "vkubelet_pod_ips", config.get("vkubelet_pod_ips", []))
    template = replace_list_placeholder(template, "custom_metrics_ports", config.get("custom_metrics_ports", []))
    
    # Clean up any leftover placeholders (e.g., for optional fields)
    template = re.sub(r"{% if .* %}(.*?){% endif %}", "", template, flags=re.DOTALL)
    template = re.sub(r"{% for .* %}(.*?){% endfor %}", "", template, flags=re.DOTALL)

    return template

def replace_list_placeholder(template, placeholder, values):
    """
    Replace list placeholders in the template.
    """
    if values:
        list_items = "\n".join([f"    - {value}" for value in values])
        template = re.sub(rf"{{{{ {placeholder} }}}}", list_items, template)
    else:
        template = re.sub(rf"{{% if {placeholder} %}}.*{{% endif %}}", "", template, flags=re.DOTALL)
    return template

def generate_node_config(config_file, output_file):
    # Load the template file and site configuration
    with open(SITE_CONFIG_TEMPLATE, 'r') as f:
        template = f.read()

    config = loadfn(config_file)

    # Replace placeholders with values from the configuration
    final_config = replace_placeholders(template, config)

    # Save the final configuration to a YAML file
    with open(output_file, 'w') as f:
        f.write(final_config)

    print(f"Generated {output_file} from {config_file} using template {SITE_CONFIG_TEMPLATE}")

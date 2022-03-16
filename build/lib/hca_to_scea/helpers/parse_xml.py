
def get_experiment_pkg_objects(xml_content):
    """Get experiment package objects from xml."""
    for experiment_package in xml_content.findall('EXPERIMENT_PACKAGE'):
        yield experiment_package

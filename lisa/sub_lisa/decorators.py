def singleton(class_):
    """
    Singleton decorator for classes.

    Ensures only one instance of the decorated class is created. Subsequent calls to create an instance of the class will return the same instance.

    Args:
        class_ (type): The class to be decorated as a singleton.

    Returns:
        function: A function that returns the singleton instance of the class.
    """
    instances = {}

    def get_class(*args, **kwargs):
        if class_ not in instances:
            instances[class_] = class_(*args, **kwargs)
        return instances[class_]
    
    return get_class      
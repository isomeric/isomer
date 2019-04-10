from isomer.database import db_log


def profile(schemaname='sensordata', profiletype='pjs'):
    """Profiles object model handling with a very simple benchmarking test"""

    db_log("Profiling ", schemaname)

    schema = schemastore[schemaname]['schema']

    db_log("Schema: ", schema, lvl=debug)

    testclass = None

    if profiletype == 'formal':
        db_log("Running formal benchmark")
        testclass = formal.model_factory(schema)
    elif profiletype == 'pjs':
        db_log("Running PJS benchmark")
        try:
            import python_jsonschema_objects as pjs
        except ImportError:
            db_log("PJS benchmark selected but not available. Install "
                   "python_jsonschema_objects (PJS)")
            return

        db_log()
        builder = pjs.ObjectBuilder(schema)
        ns = builder.build_classes()
        pprint(ns)
        testclass = ns[schemaname]
        db_log("ns: ", ns, lvl=warn)

    if testclass is not None:
        db_log("Instantiating elements...")
        for i in range(100):
            testclass()
    else:
        db_log("No Profiletype available!")

    db_log("Profiling done")

# profile(schemaname='sensordata', profiletype='formal')

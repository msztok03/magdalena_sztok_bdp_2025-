import duckdb
import pandas as pd
import great_expectations as gx
from great_expectations.core.expectation_configuration import ExpectationConfiguration


def main():

    con = duckdb.connect("spatial_duck.db")
    df = con.execute("SELECT * FROM bike_paths LIMIT 5000").df()

    context = gx.get_context()

  
    try:
        datasource = context.datasources["pandas_source"]
    except KeyError:
        datasource = context.sources.add_pandas("pandas_source")

  
    asset = datasource.add_dataframe_asset(
        name="bike_paths_asset",
        dataframe=df
    )


    batch_request = asset.build_batch_request()


    suite_name = "bike_paths_suite"

    try:
        suite = context.get_expectation_suite(expectation_suite_name=suite_name)
    except:
        suite = context.add_or_update_expectation_suite(expectation_suite_name=suite_name)


    suite.expectations = []  

    suite.expectations.append(
        ExpectationConfiguration(
            expectation_type="expect_column_to_exist",
            kwargs={"column": "geometry"}
        )
    )

    suite.expectations.append(
        ExpectationConfiguration(
            expectation_type="expect_column_values_to_not_be_null",
            kwargs={"column": "geometry"}
        )
    )

    suite.expectations.append(
        ExpectationConfiguration(
            expectation_type="expect_table_row_count_to_be_between",
            kwargs={"min_value": 11}
        )
    )


    context.add_or_update_expectation_suite(expectation_suite=suite)

    validator = context.get_validator(
        batch_request=batch_request,
        expectation_suite_name=suite_name
    )


    results = validator.validate()

    print("\n===== WYNIKI WALIDACJI =====\n")
    print(results)

    context.build_data_docs()
    print("\nRaport: great_expectations/uncommitted/data_docs/local_site/index.html")


if __name__ == "__main__":
    main()

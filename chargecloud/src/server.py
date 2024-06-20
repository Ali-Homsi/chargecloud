from bottle import run, route, HTTPResponse, request


from chargecloud_repository import ChargeCloudRepository

repo = ChargeCloudRepository(
    "chargecloud/simulation/chargecloud.db"
)


@route("/statistics", method="POST")
def get():
    from_ts = request.json["from_ts"]
    to_ts = request.json["to_ts"]
    statistic_type = request.json["statistic_type"]
    statistic_level = request.json["statistic_level"]
    abstraction_level = request.json["abstraction_level"]
    repo.fetch_statistics_by_datetime_range(
        statistic_type=statistic_type,
        statistic_level=statistic_level,
        from_ts=from_ts,
        to_ts=to_ts,
        abstraction_level=abstraction_level,
    )

    return HTTPResponse(status=200, body={"some": "body"})


if __name__ == "__main__":
    run(host="0.0.0.0", port=8185)

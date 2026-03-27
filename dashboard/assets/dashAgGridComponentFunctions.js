var dagcomponentfuncs = (window.dashAgGridComponentFunctions =
    window.dashAgGridComponentFunctions || {});

dagcomponentfuncs.ProductLink = function (props) {
    if (!props.value) return "";
    return React.createElement(
        "a",
        {
            href: "/product?hs6=" + props.value,
            style: { color: "#2563eb", textDecoration: "none" },
        },
        props.value
    );
};

dagcomponentfuncs.CountryLink = function (props) {
    if (!props.value) return "";
    return React.createElement(
        "a",
        {
            href:
                "/country?iso3=" +
                (props.data && props.data.importer_iso3
                    ? props.data.importer_iso3
                    : ""),
            style: { color: "#2563eb", textDecoration: "none" },
        },
        props.value
    );
};

dagcomponentfuncs.TrendSparkline = function (props) {
    var vals = props.value;
    if (!vals || vals.length === 0) {
        return React.createElement("span", null, "");
    }
    var w = 60, h = 20, n = vals.length;
    var points = vals
        .map(function (v, i) {
            var x = n > 1 ? (i / (n - 1)) * w : w / 2;
            var y = (1 - v) * 18 + 1;
            return x.toFixed(1) + "," + y.toFixed(1);
        })
        .join(" ");
    return React.createElement(
        "svg",
        { width: w, height: h, style: { display: "block" } },
        React.createElement("polyline", {
            points: points,
            fill: "none",
            stroke: "#2563eb",
            strokeWidth: "1.5",
            strokeLinejoin: "round",
            strokeLinecap: "round",
        })
    );
};

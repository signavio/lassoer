require(readr)
require(stringr)

#' Help page title
#'
#' A couple of lines of description about the function(s).
#' If you want to include code, use \code{my_code()}.
#' @param col_spec Contains the name of the SQL Data type
#' and special formatting instructions in paranthesis
#' @return Return a strftime formatted string that
#' can be used by parse_date() 
#' @note Describe how the algorithm works, or if the function has
#' any quirks here.
#' @author Stefano Da Ros
#' @examples
#' #R code run by the example function
#' \dontrun{
#' #R code that isn't run by example or when the package is built
#' }
#' @keywords misc
#' @export
as.sql_ddl <- function(col_spec, locale=default_locale()) {
  type <- class(col_spec)[1]
  format <- col_spec$format
  if (is.null(format) || format == '') {
    format <- ''
  } else {
    format <- glue::glue("('{to_reference(format)}')")
  }
  switch(
    type,
    "collector_character" = "VARCHAR",
    "collector_date" = glue::glue("DATE{format}",na=''),
    "collector_datetime" = glue::glue("TIMESTAMP{format}",na=''),
    "collector_double" = "DECIMAL(38,20)",
    "collector_integer" = "BIGINT",
    # Set collector_logical explicitly to VARCHAR and not BOOLEAN
    # because read_delim()'s auto type detection incorrectly
    # expects columns which contain many NA values
    # interspersed with some real values
    # to be of type BOOLEAN
    "collector_logical" = "VARCHAR",
    "collector_number" = ifelse(locale$grouping_mark == ',' && locale$decimal_mark == '.',
				"NUMERIC",
				glue::glue("NUMERIC('8{group}999{dec}99')",
                                           group = locale$grouping_mark,
                                           dec = locale$decimal_mark,
                                           na='')),
    "collector_time" = glue::glue("TIME{format}",na=''),
  )
}
to_reference<- function(format) {
    str_replace_all(
    format,
    c("%y" = "06", "%Y" = "2006", "%m" = "01", "%b" = "Jan",
      "%B" = "January", "%d" = "02", "%I" = "03", "%H" = "15",
      "%M" = "04", "%OS" = "05.000", "%p" = "PM")
  )
}

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
as.sql_ddl <- function(col_spec) {
  type <- class(col_spec)[1]
  format <- col_spec$format
  switch(
    type,
    "collector_character" = "VARCHAR",
    "collector_date" = glue::glue("DATE('{to_reference(format)}')",na=''),
    "collector_datetime" = glue::glue("TIMESTAMP('{to_reference(format)}')",na=''),
    "collector_double" = "DECIMAL(38,20)",
    "collector_integer" = "INTEGER",
    "collector_logical" = "BOOLEAN",
    "collector_number" = "NUMERIC(38,20)",
    "collector_time" = glue::glue("TIME('{to_reference(format)}')",na=''),
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
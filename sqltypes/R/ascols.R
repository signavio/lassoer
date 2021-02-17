require(readr)
require(stringr)
#' Convert between col_spec and SQL DDL
#'
#' A couple of lines of description about the function(s).
#' If you want to include code, use \code{my_code()}.
#' @param sql_type Contains the name of the SQL Data type
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
as.cols<- function(sql_type) {
  type <-  str_match(sql_type, "(\\w+)\\(?\"?'?([^)|'|\"]*)\"?'?\\)?")[2]
  format <-  str_match(sql_type, "(\\w+)\\(?\"?'?([^)|'|\"]*)\"?'?\\)?")[3]
  switch (
    str_to_lower(type),
    "boolean" = col_logical(),
    "date" = {
      if(format == '') return(col_date())
      is_ymd <- str_detect(format, "^2?0?06")
      if (is_ymd) return(in_ymd_hms(format))
      is_mdy <- str_detect(format, "^(01|[Jj]anuary|[Jj]an)[:punct:]?[:space:]?02")
      if (is_mdy) return(in_mdy_hms(format))
      is_dmy <- str_detect(format, "^02[:punct:]?[:space:]?(01|[Jj]anuary|[Jj]an)")
      if (is_dmy) return(in_dmy_hms(format))
      stop(glue::glue("Unable to determine year/month/day order in format string `{format}`"))
    },
    "decimal" = col_number(),
    "float" = col_double(),
    "double" = col_double(),
    "integer" = col_integer(),
    "numeric" = col_number(),
    "time" = {
      if(format == '') return(col_time())
      return(in_ymd_hms(format))
    },
    "varchar" = col_character(),
    "timestamp" = {
      if(format == '') return(col_datetime())
      is_ymd <- str_detect(format, "^2?0?06")
      if (is_ymd) return(in_ymd_hms(format))
      is_mdy <- str_detect(format, "^(01|[Jj]anuary|[Jj]an)[:punct:]?[:space:]?02")
      if (is_mdy) return(in_mdy_hms(format))
      is_dmy <- str_detect(format, "^02[:punct:]?[:space:]?(01|[Jj]anuary|[Jj]an)")
      if (is_dmy) return(in_dmy_hms(format))
      stop(glue::glue("Unable to determine year/month/day order in format string `{format}`"))
    },
  )
}
in_ymd_hms <- function(format) {
  re <- str_c(
    "(2006|06)?", # Year
    "([:punct:]?[:space:]?)?", # Separator
    "(01|[Jj]anuary|[Jj]an)?", # Month
    "([:punct:]?[:space:]?)?", # Separator
    "(02)?", # Day
    "([T|\\s])?", # 'T' or space (date/time separator)
    "(03|3|15)?", # Hour
    "([:punct:])?", # Separator
    "(04)?", # Minute
    "([:punct:])?", # Separator
    "(\\d\\d\\.?(0{1,6})?)?", # Seconds
    "(AM|PM)?" # AM or PM
  )
  match <- str_match(format, re)
  year <- switch (
    match[2],
    "06" = "%y",
    "2006" = "%Y",
    "NA" = NA,
  )
  sep1 <- match[3]
  month <- switch (
    as.character(str_length(match[4])),
    "2" = "%m",
    "3" = "%b",
    "7" = "%B",
    "NA" = NA,
  )
  sep2 <- match[5]
  day <- switch (
    match[6],
    "02" = "%d",
    "NA" = NA
  )
  dt_sep <- match[7]
  hours <- match[8]
  sep3 <- match[9]
  minutes <- match[10]
  sep4 <- match[11]
  seconds <- match[12]
  am_pm <- match[14]

  no_match <- is.na(match[1])
  bad_year <- !is.na(year) && (year != "2006" || year != "06")
  bad_month <- is.na(month)
  bad_day <- is.na(day)
  missing_minutes <- !is.na(hours) && is.na(minutes)
  bad_minutes <- missing_minutes || (!is.na(minutes) && minutes != "04")
  bad_seconds <- !is.na(seconds) && !str_starts(seconds, "05")
  missing_am_pm <- (!is.na(hours) && is.na(am_pm)) && (hours == "03" || hours == "3")
  if (no_match) {
    stop(glue::glue("Unable to match format string `{format}`"))
  }
  if (bad_year && (bad_month || bad_day)) {
    stop(glue::glue("Format string contains malformed year, month or day `{format}` "))
  }
  if (bad_minutes || bad_seconds) {
    stop(glue::glue("Format string contains malformed minutes and/or seconds `{format}`"))
  }
  if (missing_am_pm) {
    stop(glue::glue("Format string is missing AM/PM indicator `{format}`"))
  }
  if (is.na(hours)) {
    hms <- NA
  } else if (is.na(seconds)) {
    if (!is.na(am_pm)) {
      hms <- glue::glue("%I{sep3}%M%p",.na='')
    } else {
      hms <- glue::glue("%H{sep3}%M",.na='')
    }
  } else {
    if (!is.na(am_pm)) {
      hms <- glue::glue("%I{sep3}%M{sep4}%OS%p",.na='')
    } else {
      hms <- glue::glue("%H{sep3}%M{sep4}%OS",.na='')
    }
  }
  ymd_hms = glue::glue('{year}{sep1}{month}{sep2}{day}{dt_sep}{hms}',.na='')

  if (is.na(year)) {
  return(col_time(format=ymd_hms))
  }
  if (is.na(hms)) {
  return(col_date(format=ymd_hms))
  }
  return(col_datetime(format=ymd_hms))
}
in_dmy_hms <- function(format) {
  re <- str_c(
    "(02)?", # Day
    "([:punct:]?[:space:]?)?", # Separator
    "(01|[Jj]anuary|[Jj]an)?", # Month
    "([:punct:]?[:space:]?)?", # Separator
    "(2006|06)?", # Year
    "([T|\\s])?", # 'T' or space (date/time separator)
    "(03|3|15)?", # Hour
    "([:punct:])?", # Separator
    "(04)?", # Minute
    "([:punct:])?", # Separator
    "(\\d\\d\\.?(0{1,6})?)?", # Seconds
    "(AM|PM)?" # AM or PM
  )
  match <- str_match(format, re)
  day <- switch (
    match[2],
    "02" = "%d",
    "NA" = NA,
  )
  sep1 <- match[3]
  month <- switch (
    as.character(str_length(match[4])),
    "2" = "%m",
    "3" = "%b",
    "7" = "%B",
    "NA" = NA,
  )
  sep2 <- match[5]
  year <- switch (
    match[6],
    "06" = "%y",
    "2006" = "%Y",
    "NA" = NA,
  )
  dt_sep <- match[7]
  hours <- match[8]
  sep3 <- match[9]
  minutes <- match[10]
  sep4 <- match[11]
  seconds <- match[12]
  am_pm <- match[14]
  if (is.na(hours)) {
    hms <- NA
  } else if (is.na(seconds)) {
    if (!is.na(am_pm)) {
      hms <- glue::glue("%I{sep3}%M%p",.na='')
    } else {
      hms <- glue::glue("%H{sep3}%M",.na='')
    }
  } else {
    if (!is.na(am_pm)) {
      hms <- glue::glue("%I{sep3}%M{sep4}%OS%p",.na='')
    } else {
      hms <- glue::glue("%H{sep3}%M{sep4}%OS",.na='')
    }
  }
  no_match <- is.na(match[1])
  bad_year <- is.na(year)
  bad_month <- is.na(month)
  bad_day <- is.na(day)
  bad_dmy <- bad_year || bad_month || bad_day
  bad_hour <- is.na(hours)
  bad_minutes <- !is.na(hours) && is.na(minutes)
  bad_seconds <- !is.na(seconds) && !str_starts(seconds, "05")
  bad_hms <- bad_hour || bad_minutes || bad_seconds
  missing_am_pm <- (!is.na(hours) && is.na(am_pm)) && (hours == "03" || hours == "3")
  if (no_match) {
    stop(glue::glue("Unable to match format string `{format}`"))
  }
  if (bad_dmy && is.na(hms)) {
    stop(glue::glue("Format string contains malformed year, month or day `{format}` "))
  }
  if (bad_minutes || bad_seconds) {
    stop(glue::glue("Format string contains malformed minutes and/or seconds `{format}`"))
  }
  if (missing_am_pm) {
    stop(glue::glue("Format string is missing AM/PM indicator `{format}`"))
  }
  
  dmy_hms = glue::glue('{day}{sep1}{month}{sep2}{year}{dt_sep}{hms}',.na='')

  if (is.na(year)) {
  return(col_time(format=dmy_hms))
  }
  if (is.na(hms)) {
  return(col_date(format=dmy_hms))
  }
  return(col_datetime(format=dmy_hms))
}
in_mdy_hms <- function(format) {
  re <- str_c(
    "(01|[Jj]anuary|[Jj]an)?", # Month
    "([:punct:]?[:space:]?)?", # Separator
    "(02)?", # Day
    "([:punct:]?[:space:]?)?", # Separator
    "(2006|06)?", # Year
    "([T|\\s])?", # 'T' or space (date/time separator)
    "(03|3|15)?", # Hour
    "([:punct:])?", # Separator
    "(04)?", # Minute
    "([:punct:])?", # Separator
    "(\\d\\d\\.?(0{1,6})?)?", # Seconds
    "(AM|PM)?" # AM or PM
  )
  match <- str_match(format, re)
  month <- switch (
    as.character(str_length(match[2])),
    "2" = "%m",
    "3" = "%b",
    "7" = "%B",
    "NA" = NA,
  )
  sep1 <- match[3]
  day <- switch (
    match[4],
    "02" = "%d",
    "NA" = NA,
  )
  sep2 <- match[5]
  year <- switch (
    match[6],
    "06" = "%y",
    "2006" = "%Y",
    "NA" = NA,
  )
  dt_sep <- match[7]
  hours <- match[8]
  sep3 <- match[9]
  minutes <- match[10]
  sep4 <- match[11]
  seconds <- match[12]
  am_pm <- match[14]
  if (is.na(hours)) {
    hms <- NA
  } else if (is.na(seconds)) {
    if (!is.na(am_pm)) {
      hms <- glue::glue("%I{sep3}%M%p",.na='')
    } else {
      hms <- glue::glue("%H{sep3}%M",.na='')
    }
  } else {
    if (!is.na(am_pm)) {
      hms <- glue::glue("%I{sep3}%M{sep4}%OS%p",.na='')
    } else {
      hms <- glue::glue("%H{sep3}%M{sep4}%OS",.na='')
    }
  }
  no_match <- is.na(match[1])
  bad_year <- is.na(year)
  bad_month <- is.na(month)
  bad_day <- is.na(day)
  bad_dmy <- bad_year || bad_month || bad_day
  bad_hour <- is.na(hours)
  bad_minutes <- !is.na(hours) && is.na(minutes)
  bad_seconds <- !is.na(seconds) && !str_starts(seconds, "05")
  bad_hms <- bad_hour || bad_minutes || bad_seconds
  missing_am_pm <- (!is.na(hours) && is.na(am_pm)) && (hours == "03" || hours == "3")
  if (no_match) {
    stop(glue::glue("Unable to match format string `{format}`"))
  }
  if (bad_dmy && is.na(hms)) {
    stop(glue::glue("Format string contains malformed year, month or day `{format}` "))
  }
  if (bad_minutes || bad_seconds) {
    stop(glue::glue("Format string contains malformed minutes and/or seconds `{format}`"))
  }
  if (missing_am_pm) {
    stop(glue::glue("Format string is missing AM/PM indicator `{format}`"))
  }
  
  mdy_hms = glue::glue('{month}{sep1}{day}{sep2}{year}{dt_sep}{hms}',.na='')

  if (is.na(year)) {
  return(col_time(format=mdy_hms))
  }
  if (is.na(hms)) {
  return(col_date(format=mdy_hms))
  }
  return(col_datetime(format=mdy_hms))
}

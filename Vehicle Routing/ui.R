
ui <- shinyUI(

    navbarPage(
      
      # Application title
      title = div(tags$img(src="routing2.png", style="margin-top: -15px;", width = '60', height='50'), ""),
      windowTitle="ROUTING APPS",
      position = "fixed-top",
      theme = shinytheme("darkly"),
      br(),
      
      ################################## CVRP ##################################
      
        tabPanel(
          "DAY TRIP PLANNER",
          
          # Load modules
          useShinyjs(),
          
          br(),
          br(),
          hr(),
          
          sidebarLayout(
            sidebarPanel(
              
              width = 4,
              
              selectInput("type",
                          "Route suggestion type:",
                          c("Choose visits","Suggest visits", "Choose & Suggest")),
              
              selectInput("stpoint",
                          "Choose starting point:",
                          c('Four Streets Athens', '360 Degrees Hotel', 'Acropolis View Hotel')),
              
              conditionalPanel(condition = "input.type == 'Choose visits'",
                                 pickerInput(
                                 inputId="visit_in",
                                 label="Choose visits:",
                                 c('Parthenon',
                                   'Acropolis Museum',
                                   'Athens National Garden',
                                   'Ancient Agora of Athens',
                                   'National Archaeological Museum',
                                   'Lycabettus Hill',
                                   'Odeon of Herodes Atticus',
                                   'Roman Forum of Athens (Roman Agora)',
                                   'Temple of Hephaestus - part of Agora',
                                   'Hymettus, Kesariani & Vyronas Aesthetic Forest',
                                   'Kerameikos Archaeological Site'),
                                 multiple = TRUE),
                               ),
             
              conditionalPanel(condition = "input.type == 'Suggest visits'",
                               splitLayout(
                                 numericInput("n_of_visits",
                                              "# of visits:",
                                              min = 1,
                                              value = 4,
                                              step = 1),
                                 numericInput("available_hours",
                                              "Available hours:",
                                              min = 1,
                                              value = 8,
                                              step = 1),
                               )),
              
              conditionalPanel(condition = "input.type == 'Choose & Suggest'",
                               splitLayout(
                                 numericInput("n_of_visits",
                                              "# of visits:",
                                              min = 1,
                                              value = 4,
                                              step = 1),
                                 numericInput("available_hours",
                                              "Available hours:",
                                              min = 1,
                                              value = 8,
                                              step = 1)
                                 
                               )),
              
              conditionalPanel(condition = "input.type == 'Choose & Suggest'",
                               
                               pickerInput("path_contains",
                                           "Must Contain:",
                                           c('Parthenon',
                                             'Acropolis Museum',
                                             'Athens National Garden',
                                             'Ancient Agora of Athens',
                                             'National Archaeological Museum',
                                             'Lycabettus Hill',
                                             'Odeon of Herodes Atticus',
                                             'Roman Forum of Athens (Roman Agora)',
                                             'Temple of Hephaestus - part of Agora',
                                             'Hymettus, Kesariani & Vyronas Aesthetic Forest',
                                             'Kerameikos Archaeological Site'
                                           ), 
                                           multiple=TRUE
                               ),
                               
                               tags$head(
                                 tags$style(
                                   HTML(".shiny-split-layout > div {overflow: visible;}")))
                               
              ),
              
              awesomeRadio(
                inputId = "transport_input",
                label = NULL, 
                choices = c("Walking", "Driving"),
                inline = TRUE,
              ),
              
              column(
                12,
                
                column(
                  6,
                  splitLayout(
                
                  dateInput("date_input_day", 'Select date:', width='120px'),
                  
                  timeInput("date_input_time", 'Select time:', value = strptime("09:00:00", "%T"),
                             minute.steps = 15, seconds = FALSE)),
                  
                ),
                
                column(
                  6,
                  
                  materialSwitch("rest_options", "Optional rest parameters", right=TRUE, status = "primary"),
                  
                  conditionalPanel(condition = "input.rest_options == true",
                                   
                                   awesomeRadio(inputId="rest_type", 
                                                label='Rest type',
                                                choices=c("Distance walked", "Time elapsed"), 
                                                inline=TRUE,
                                                checkbox = TRUE),
                                   
                                   conditionalPanel(condition = "input.rest_type == 'Distance walked'",
                                                    
                                                    splitLayout(
                                                      numericInput(inputId="rest_distance_in",
                                                                   "Distance (km):",
                                                                   min = 1,
                                                                   value = 3,
                                                                   step = 0.2),
                                                      numericInput("rest_duration_in",
                                                                   "Duration (mins):",
                                                                   min = 10,
                                                                   value = 30,
                                                                   step = 5)
                                                    )
                                   ),
                                   
                                   conditionalPanel(condition = "input.rest_type == 'Time elapsed'",
                                                    
                                                    splitLayout(
                                                      numericInput(inputId="rest_time_in",
                                                                   "Time (hours):",
                                                                   min = 1,
                                                                   value = 3,
                                                                   step = 0.5),
                                                      numericInput("rest_duration_in",
                                                                   "Duration (mins):",
                                                                   min = 10,
                                                                   value = 30,
                                                                   step = 5)
                                                    )
                                   )
                                   
                  ),
                  
                )
                
              ),
              
              hr(),

              tags$head(
                tags$style(HTML('#run_calculation{color:black}'))
              ),

              actionBttn("run_calculation", "Calculate routes", style = "fill", color = "success", block=TRUE),
              
              hr(),
              
              div(span(textOutput("no_routes"),
                     style="color:#000000 ;font-weight: normal;font-size: 14px")
              ),
              
              plotlyOutput("myVistime"),
              
              br(),
              
              splitLayout(
                cellWidths = c("65%", "35%"),
                conditionalPanel(condition = "input.type == 'Suggest visits' || input.type == 'Choose & Suggest'",
                               radioGroupButtons(
                                 inputId = "chosen_route",
                                 choiceNames = c("Route 1", "Route 2", "Route 3", "Route 4", "Route 5"),
                                 choiceValues = c(1, 2, 3, 4, 5),
                                 status = "primary")
                ),
                
                
                switchInput(inputId = "restau_switch", label = "Show restaurants",
                            labelWidth = "140px")
                
                
              ),
              
              
            ),
            
            
            mainPanel(
              
              width = 8,

              fluidRow(
                
                column(
                  
                  3,
                  
                  div(class="panel panel-default", 
                      style = "background-color: rgb(80, 185, 99); box-shadow: 2px 2px 2px 1px #d1d1d1; opacity: 0.9;",
                      div(class="panel-body",  width = "600px",
                          align = "center",
                          h4(tags$b("Start time", style="color:#FFFFFF")
                          ),
                          
                          div(
                            span(textOutput("start_time_kpi"),
                                 style="color:#FFFFFF;font-weight: bold;font-size: 26px")
                          )
                          
                      )
                  )
                ),
                
                column(
                  
                  3,
                  
                  div(class="panel panel-default", 
                      style = "background-color: rgb(80, 185, 99); box-shadow: 2px 2px 2px 1px #d1d1d1; opacity: 0.9;",
                      div(class="panel-body",  width = "600px",
                          align = "center",
                          h4(tags$b("End time", style="color:#FFFFFF")
                          ),
                          
                          div(
                            span(textOutput("eta_finish_kpi"),
                                 style="color:#FFFFFF;font-weight: bold;font-size: 26px")
                            )
                          
                      )
                  )
                ),
                
                column(
                  
                  3,
                  
                  div(class="panel panel-default", 
                      style = "background-color: rgb(230, 133, 55); box-shadow: 2px 2px 2px 1px #d1d1d1; opacity: 0.9;",
                      div(class="panel-body",  width = "600px",
                          align = "center",
                          h4(tags$b("Total duration", style="color:#FFFFFF")
                          ),
                          
                          div(
                            span(textOutput("total_time_kpi"), 
                                 style="color:#FFFFFF;font-weight: bold;font-size: 26px")
                          )
                      )
                  )
                ),
                
                column(
                  
                  3,
                  
                  div(class="panel panel-default", 
                      style = "background-color: rgb(230, 133, 55); box-shadow: 2px 2px 2px 1px #d1d1d1; opacity: 0.9;",
                      div(class="panel-body",  width = "600px",
                          align = "center",
                          h4(tags$b("Total distance", style="color:#FFFFFF")
                          ),
                          
                          div(
                            span(textOutput("total_distance_kpi"), 
                                 style="color:#FFFFFF;font-weight: bold;font-size: 26px")
                          )
                      )
                  )
                ),
                
              ),
              

              fillPage(

                leafletOutput("mymap", height = '80vh')

              ),
            

            )
            
          )
        ),
      
      ################################## CVRP ##################################
      
      tabPanel(
        "GARBAGE TRUCK ROUTING",
        
        # Load modules
        useShinyjs(),
        
        br(),
        br(),
        hr(),
        
        column(
          
          class="panel panel-default",
          # style="background-color: #E9E9E9; box-shadow: 2px 2px 2px 1px #d1d1d1;", # 234, 250, 241 
          
          width = 3,
          
          br(),
          
          checkboxGroupButtons(
            inputId = "active_depots",
            choiceNames = c("Depot 1", "Depot 2", "Depot 3"),
            choiceValues = c(0, 1, 2),
            status = "primary"),
          
          splitLayout(
            
            numericInput("date_input_time_cvrp", 'Start time:', min=0, max=23, value=14, step=1),
            
            awesomeRadio(
              inputId = "search_fill",
              label = "Smart search", 
              choices = c('On', 'Off'),
              selected = "Off",
              inline = TRUE, 
              status = "success"
            )
            
          ),
          
          
          
          hr(),
          
          tags$head(tags$style(HTML('#run_calculation{color:black}'))),
          
          actionBttn("run_cvrp", "Calculate routes", style = "fill", color = "success", block=TRUE),
          
          br(),
          
          div(span(textOutput("no_routes_cvrp"),
                   style="color:#DA3232 ;font-weight: normal;font-size: 18px")
          ),
          
          uiOutput("selectv_render"),
          
          br(),
          
          plotOutput('distance_bar', height='250px'),
          
          plotOutput('load_bar', height='250px'),
          
          br(),
          
        ),
        
        
        column(
          
          width = 9,
          
          fluidRow(
            
            column(
              
              3,
              
              div(class="panel panel-default",
                  style = "background-color: rgb(80, 185, 99); box-shadow: 2px 2px 2px 1px #d1d1d1; opacity: 0.9;",
                  div(class="panel-body",  width = "600px",
                      align = "center",
                      h4(tags$b("Vehicles used", style="color:#FFFFFF")
                      ),
                      
                      div(
                        span(textOutput("total_vehicles_kpi"),
                             style="color:#FFFFFF;font-weight: bold;font-size: 26px")
                      )
                      
                  )
              )
            ),
            
            column(
              
              3,
              
              div(class="panel panel-default",
                  style = "background-color: rgb(80, 185, 99); box-shadow: 2px 2px 2px 1px #d1d1d1; opacity: 0.9;",
                  div(class="panel-body",  width = "600px",
                      align = "center",
                      h4(tags$b("Distance travelled", style="color:#FFFFFF")
                      ),
                      
                      div(
                        span(textOutput("total_distance_kpi_cvrp"),
                             style="color:#FFFFFF;font-weight: bold;font-size: 26px")
                      )
                      
                  )
              )
            ),
            
            column(
              
              3,
              
              div(class="panel panel-default",
                  style = "background-color: rgb(80, 185, 99); box-shadow: 2px 2px 2px 1px #d1d1d1; opacity: 0.9;",
                  div(class="panel-body",  width = "600px",
                      align = "center",
                      h4(tags$b("Load collected", style="color:#FFFFFF")
                      ),
                      
                      div(
                        span(textOutput("total_load_kpi"),
                             style="color:#FFFFFF;font-weight: bold;font-size: 26px")
                      )
                      
                  )
              )
            ),
            
            column(
              
              3,
              
              div(class="panel panel-default",
                  style = "background-color: rgb(80, 185, 99); box-shadow: 2px 2px 2px 1px #d1d1d1; opacity: 0.9;",
                  div(class="panel-body",  width = "600px",
                      align = "center",
                      h4(tags$b("Fuel consumed", style="color:#FFFFFF")
                      ),
                      
                      div(
                        span(textOutput("total_fuel_kpi"),
                             style="color:#FFFFFF;font-weight: bold;font-size: 26px")
                      )
                  )
              )
            ),
            
          ),
          
          fillPage(
            
            leafletOutput("mymap_cvrp", height = '78vh')
            
          ),
          
          
        )
        
        
      )
    )
)

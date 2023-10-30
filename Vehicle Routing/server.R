# Define server logic required to draw a histogram
server <- shinyServer(function(input, output, session) {
  
  ################################## TSP ##################################
  reactive_choose <- reactiveValues(optimal_info_df=NULL, route_info_all=NULL, gjson=NULL, flag=NULL)
  
  reactive_suggest <- reactiveValues(suggestions_leaflet=NULL, suggestions_gant=NULL, suggestions_gjson=NULL)
  
  observeEvent(input$run_calculation, {
    
    shinyalert(title = "Please wait", text = "", type = "",
               closeOnEsc = FALSE, closeOnClickOutside = F, showConfirmButton = F, 
               showCancelButton = F,
               timer = 0, imageUrl = "loader_col2.gif",
               imageWidth = 200, imageHeight = 200, 
               animation = F,
               size='xs',
               inputId = "loader_test")

    pydate <-  str_split(paste(input$date_input_day, input$date_input_time), " ")
    pydate <-  paste(pydate[[1]][1], " ", pydate[[1]][3])
    
    if (input$type == "Choose visits"){
      starting_hotel <- input$stpoint
      visits_chosen <- input$visit_in

      if (length(visits_chosen)==1){
        chosen_data <- choose_visits(start=starting_hotel, visits=list(visits_chosen))
      }
      else {
        chosen_data <- choose_visits(start=starting_hotel, visits=visits_chosen)
      }
      
      if (input$rest_options==TRUE){
        
        if (input$rest_type == 'Distance walked'){
          
          rest_time_in <- 9999999
          rest_distance_in <- input$rest_distance_in[1]*1000
          rest_duration_in <- input$rest_duration_in[1]*60
          df <- solve_tsp(st_idx=chosen_data[[1]], routes=chosen_data[[2]],
                          rest_time=rest_time_in, rest_distance=rest_distance_in,
                          rest_length=rest_duration_in, start_time=pydate, trans_type=input$transport_input)
        }
        
        if (input$rest_type == 'Time elapsed'){
          
          rest_time_in <- input$rest_time_in[1]*3600
          rest_distance_in <- 9999999
          rest_duration_in <- input$rest_duration_in[1]*60
          df <- solve_tsp(st_idx=chosen_data[[1]], routes=chosen_data[[2]],
                          rest_time=rest_time_in, rest_distance=rest_distance_in,
                          rest_length=rest_duration_in, start_time=pydate, trans_type=input$transport_input)
        }
        
      }
      
      if (input$rest_options==FALSE){
        df <- solve_tsp(st_idx=chosen_data[[1]], routes=chosen_data[[2]],
                              rest_time=9999999, rest_distance=9999999,
                              rest_length=0, start_time=pydate, trans_type=input$transport_input)
      }

      solution_list <- get_solution(final_df=df, st_idx=chosen_data[[1]],
                                    type_flag='optimal', trans_type=input$transport_input)
      
      reactive_choose$optimal_info_df <- solution_list[[1]]
      reactive_choose$route_info_all <- solution_list[[2]]
      reactive_choose$gjson <- solution_list[[3]]
      
      reactive_choose$gant_data <- gant_table(reactive_choose$route_info_all, type_flag='optimal', trans_type=input$transport_input)
      
      reactive_choose$flag <- NULL
      reactive_choose$flag <- 'choose'
      
    }
    
    if (input$type == "Suggest visits"){
      
      starting_hotel <- input$stpoint
      nofvis <- input$n_of_visits
      hoursavail <- input$available_hours
      suggestion_data <- suggest_visits(stpoint=starting_hotel, n_of_visits=nofvis,
                                        available_hours=hoursavail)
      
      if (input$rest_options==TRUE){
        
        if (input$rest_type == 'Distance walked'){
          rest_time_in <- 9999999
          rest_distance_in <- input$rest_distance_in[1]*1000
          rest_duration_in <- input$rest_duration_in[1]*60
          df <- solve_tsp(st_idx=suggestion_data[[1]], routes=suggestion_data[[2]],
                          rest_time=rest_time_in, rest_distance=rest_distance_in,
                          rest_length=rest_duration_in, start_time=pydate, trans_type=input$transport_input)
        }

        if (input$rest_type == 'Time elapsed'){
          rest_time_in <- input$rest_time_in[1]*3600
          rest_distance_in <- 9999999
          rest_duration_in <- input$rest_duration_in[1]*60
          df <- solve_tsp(st_idx=suggestion_data[[1]], routes=suggestion_data[[2]],
                          rest_time=rest_time_in, rest_distance=rest_distance_in,
                          rest_length=rest_duration_in, start_time=pydate, trans_type=input$transport_input)
        }
        
      }

      if (input$rest_options==FALSE){
        df <- solve_tsp(st_idx=suggestion_data[[1]], routes=suggestion_data[[2]],
                        rest_time=9999999, rest_distance=9999999,
                        rest_length=0, start_time=pydate, trans_type=input$transport_input)
      }
      
      suggestions_list <- get_solution(final_df=df, st_idx=suggestion_data[[1]],
                                     type_flag='suggestions',
                                     trans_type=input$transport_input,
                                     available_hours=hoursavail,
                                     path_contains=list(0))
      
      reactive_suggest$suggestions_leaflet <- suggestions_list[[1]]
      reactive_suggest$route_info <- suggestions_list[[2]]
      reactive_suggest$suggestions_gjson <- suggestions_list[[3]]

      reactive_suggest$gant_data <- gant_table(reactive_suggest$route_info, type_flag='suggestions', trans_type=input$transport_input)
      
      reactive_choose$flag <- NULL
      reactive_choose$flag <- 'suggest'
      
    }
    
    if (input$type == "Choose & Suggest"){
      # limit select to nofvis
      
      starting_hotel <- input$stpoint
      nofvis <- input$n_of_visits
      hoursavail <- input$available_hours
      mustcont <- input$path_contains
      
      if (length(mustcont)==1){
        choose_suggest <- suggest_visits(stpoint=starting_hotel, n_of_visits=nofvis,
                                         available_hours=hoursavail,
                                         path_contains=list(mustcont))
      }
      
      if (length(mustcont)>1){
        choose_suggest <- suggest_visits(stpoint=starting_hotel, n_of_visits=nofvis,
                                         available_hours=hoursavail,
                                         path_contains=mustcont)
      }
      
      else {
        choose_suggest <- suggest_visits(stpoint=starting_hotel, n_of_visits=nofvis,
                                         available_hours=hoursavail)
      }

      if (input$rest_options==TRUE){
        
        if (input$rest_type == 'Distance walked'){
          rest_time_in <- 9999999
          rest_distance_in <- input$rest_distance_in[1]*1000
          rest_duration_in <- input$rest_duration_in[1]*60
          df <- solve_tsp(st_idx=choose_suggest[[1]], routes=choose_suggest[[2]],
                          rest_time=rest_time_in, rest_distance=rest_distance_in,
                          rest_length=rest_duration_in, start_time=pydate, trans_type=input$transport_input)
        }

        if (input$rest_type == 'Time elapsed'){
          rest_time_in <- input$rest_time_in[1]*3600
          rest_distance_in <- 9999999
          rest_duration_in <- input$rest_duration_in[1]*60
          df <- solve_tsp(st_idx=choose_suggest[[1]], routes=choose_suggest[[2]],
                          rest_time=rest_time_in, rest_distance=rest_distance_in,
                          rest_length=rest_duration_in, start_time=pydate, trans_type=input$transport_input)
        }
        
      }
      
      if (input$rest_options==FALSE){
        df <- solve_tsp(st_idx=choose_suggest[[1]], routes=choose_suggest[[2]],
                        rest_time=9999999, rest_distance=9999999,
                        rest_length=0, start_time=pydate, trans_type=input$transport_input)
      }
      
      suggestions_list <- get_solution(final_df=df, st_idx=choose_suggest[[1]],
                                     type_flag='suggestions',
                                     trans_type=input$transport_input,
                                     available_hours=hoursavail,
                                     path_contains=choose_suggest[[5]])
      
      reactive_suggest$suggestions_leaflet <- suggestions_list[[1]]
      reactive_suggest$route_info <- suggestions_list[[2]]
      reactive_suggest$suggestions_gjson <- suggestions_list[[3]]
      
      reactive_suggest$gant_data <- gant_table(reactive_suggest$route_info, type_flag='suggestions', trans_type=input$transport_input)
      
      reactive_choose$flag <- NULL
      reactive_choose$flag <- 'suggest'
      
    }
    
    shinyjs::delay(2, {
      shinyjs::runjs("swal.close();")
    })
    
  })
  
  observeEvent(reactive_choose$flag, {
    
    if (reactive_choose$flag=='choose'){
      
      output$no_routes <- renderText({''})
      
      dist <- reactive_choose$route_info_all['path_dist_meters'][[1]]/1000
      total_distance <- as.character(format(round(dist, 2), nsmall = 2))
      
      time_dt <- reactive_choose$route_info_all['route_time_dt'][[1]]
      total_hours <- as.character(floor(time_dt))
      total_minutes <- as.character(format(round(time_dt%%1*60, 0)))
      
      start_time <- substr(head(reactive_choose$gant_data['start'][[1]], n=1L), 12, 16)
      end_time <- substr(tail(reactive_choose$gant_data['end'][[1]], n=1L), 12, 16)
      
      output$start_time_kpi <- renderText({start_time})
      output$eta_finish_kpi <- renderText({end_time})
      output$total_distance_kpi <- renderText({paste(total_distance, " km")})
      output$total_time_kpi <- renderText({paste(total_hours, " hours", total_minutes, " minutes")})
      
      day_name <- weekdays(head(reactive_choose$gant_data['start'][[1]], n=1L))
      restau_map <- restaurants%>%
        dplyr::filter(day==day_name)
      
      output$mymap <- renderLeaflet({
        leaflet() %>%
          addProviderTiles(provider = providers$CartoDB.Voyager) %>%
          addGeoJSON(reactive_choose$gjson, fill=FALSE)%>%
          addCircleMarkers(data=reactive_choose$optimal_info_df,
            
            group = 'aois',                              
                           
            lng = ~cords_lng,
            lat = ~cords_lat,
            
            label = ~paste(stop_count, ': ', title),
            
            color = ~color,
            
            fillOpacity = 1,
            
            labelOptions = labelOptions(noHide = T, direction = 'top', textOnly = F, 
                                        style = list(
                                          "font-family" = "serif",
                                          "font-weight" = "bold",
                                          "box-shadow" = "3px 3px rgba(0,0,0,0.25)",
                                          "font-size" = "15px",
                                          "border-color" = "rgba(0,0,0,0.5)"
                                        )),
            
            popup = ~paste("<b>", title, "</b>", 
                           "<br/>Time at arrival: ", node_arrival_eest,
                           "<br/>Time at departure: ", node_departure_eest,
                           "<br/>Distance from previous visit (m): ", distance_from_previous,
                           "<br/>Cumulative walking distance (m): ", cumulative_node_dist
            )
          )%>%
          addMarkers(data = restau_map,
            
            group='restaurants',         
            
            lng = ~longitude_cords,
            lat = ~latitude_cords,
            
            label = ~title,
            
            icon = restaurant_icon,
            
            labelOptions = labelOptions(noHide = F, direction = 'top', textOnly = F, 
                                        style = list(
                                          "font-family" = "serif",
                                          "font-weight" = "bold",
                                          "box-shadow" = "3px 3px rgba(0,0,0,0.25)",
                                          "font-size" = "15px",
                                          "border-color" = "rgba(0,0,0,0.5)"
                                        )),
            
            popup = ~paste("<b>", title, "</b>",
                           "<br/>Category: ", category,
                           "<br/>Rating: ", totalScore,
                           "<br/>", day_name, ": ", openinghours
            )
          )
        
      })
      
      observeEvent(list(input$restau_switch, input$mymap_zoom), {
        
        if ((input$restau_switch==TRUE) && (input$mymap_zoom > 16)){
          leafletProxy(mapId = "mymap", session = session) %>% 
            showGroup(group='restaurants')
        }
        
        if ((input$restau_switch==FALSE) || (input$mymap_zoom <= 16)){
          leafletProxy(mapId = "mymap", session = session) %>% 
            hideGroup(group='restaurants')
        }
        
        
      })
      
      
      output$myVistime <- renderPlotly({
        vistime(reactive_choose$gant_data, optimize_y=FALSE, linewidth = 30,
                col.event = "title", col.color = 'color')
      }) # show_labels = TRUE, col.group = "title"
      
    }
    
    if (reactive_choose$flag=='suggest'){
      
      if (nrow(reactive_suggest$route_info) == 0){
        
        output$no_routes <- renderText({'There were no routes found with your selected criteria'})
        
      }
      
      else {
        
        output$no_routes <- renderText({''})
        
        observeEvent(input$chosen_route, {
          
          idx <- as.integer(input$chosen_route)
          
          dist <- reactive_suggest$route_info['path_dist_meters'][[1]][idx]/1000
          total_distance <- as.character(format(round(dist, 2), nsmall = 2))
          
          time_dt <- reactive_suggest$route_info['route_time_dt'][[1]][idx]
          total_hours <- as.character(floor(time_dt))
          total_minutes <- as.character(format(round(time_dt%%1*60, 0)))
          
          start_time <- substr(head(reactive_suggest$gant_data[[idx]]['start'][[1]], n=1L), 12, 16)
          end_time <- substr(tail(reactive_suggest$gant_data[[idx]]['end'][[1]], n=1L), 12, 16)
          
          output$start_time_kpi <- renderText({start_time})
          output$eta_finish_kpi <- renderText({end_time})
          output$total_distance_kpi <- renderText({paste(total_distance, " km")})
          output$total_time_kpi <- renderText({paste(total_hours, " hours", total_minutes, " minutes")})
          
          map_dt <- reactive_suggest$suggestions_leaflet
          
          map_dt <- map_dt%>%
            dplyr::filter(route_index==idx)
          
          gjson_data <- reactive_suggest$suggestions_gjson[[idx]]
          
          day_name <- weekdays(head(reactive_suggest$gant_data[[1]]['start'][[1]], n=1L))
          restau_map <- restaurants%>%
            dplyr::filter(day==day_name)
          
          output$mymap <- renderLeaflet({
            leaflet() %>%
              addProviderTiles(provider = providers$CartoDB.Voyager) %>%
              addGeoJSON(gjson_data, fill=FALSE)%>%
              addCircleMarkers(
                data=map_dt,
                
                group = 'aois',
                
                lng = ~cords_lng,
                lat = ~cords_lat,
                
                label = ~paste(stop_count, ': ', title),
                
                color = ~color,
                
                fillOpacity = 1,
                
                labelOptions = labelOptions(noHide = T, direction = 'top', textOnly = F,
                                            style = list(
                                              "font-family" = "serif",
                                              "font-weight" = "bold",
                                              "box-shadow" = "3px 3px rgba(0,0,0,0.25)",
                                              "font-size" = "15px",
                                              "border-color" = "rgba(0,0,0,0.5)"
                                            )),
                
                popup = ~paste("<b>", title, "</b>",
                               "<br/>Time at arrival: ", node_arrival_eest,
                               "<br/>Time at departure: ", node_departure_eest,
                               "<br/>Distance from previous visit (m): ", distance_from_previous,
                               "<br/>Cumulative walking distance (m): ", cumulative_node_dist
                ),
                
              )%>%
              addMarkers(data = restau_map,
                         
                         group = 'restaurants',
                         
                         lng = ~longitude_cords,
                         lat = ~latitude_cords,
                         
                         label = ~title,
                         
                         icon = restaurant_icon,
                         
                         labelOptions = labelOptions(noHide = F, direction = 'top', textOnly = F, 
                                                     style = list(
                                                       "font-family" = "serif",
                                                       "font-weight" = "bold",
                                                       "box-shadow" = "3px 3px rgba(0,0,0,0.25)",
                                                       "font-size" = "15px",
                                                       "border-color" = "rgba(0,0,0,0.5)"
                                                     )),
                         
                         popup = ~paste("<b>", title, "</b>",
                                        "<br/>Category: ", category,
                                        "<br/>Rating: ", totalScore,
                                        "<br/>", day_name, ": ", openinghours
                         )
              )
            
          })
          
          observeEvent(list(input$restau_switch, input$mymap_zoom), {
            
            if ((input$restau_switch==TRUE) && (input$mymap_zoom > 16)){
              leafletProxy(mapId = "mymap", session = session) %>% 
                showGroup(group='restaurants')
            }
            
            if ((input$restau_switch==FALSE) || (input$mymap_zoom <= 16)){
              leafletProxy(mapId = "mymap", session = session) %>% 
                hideGroup(group='restaurants')
            }
            
            
          })
          
          output$myVistime <- renderPlotly({
            vistime(reactive_suggest$gant_data[[idx]], optimize_y=FALSE, linewidth = 30,
                    col.event = "title", col.color = 'color')
          }) # show_labels = TRUE, col.group = "title"
          
        })
        
      }
      
    }


  })
  
  ################################## CVRP ##################################
  
  
  
  react_list <- reactiveValues(veh_used=NULL, gjson=NULL, flag=NULL, previous=0)
  
  observeEvent(input$run_cvrp, {
    
    shinyalert(title = "Please wait", text = "", type = "",
               closeOnEsc = FALSE, closeOnClickOutside = F, showConfirmButton = F,
               showCancelButton = F,
               timer = 0, imageUrl = "loader_col2.gif",
               imageWidth = 500, imageHeight = 500,
               animation = F,
               inputId = "loader_test")
    
    start_time <- input$date_input_time_cvrp
    
    solution_list <- cvrp(shift=start_time, active_depots=input$active_depots)
    
    total_trip <- solution_list[[1]]
    total_trip$color <- factor(total_trip$color,levels = total_trip$color)
    fullmap_dt <- solution_list[[2]]
    react_list$gjson <- solution_list[[3]]
    reason <- solution_list[[4]]
    uncollected <- solution_list[[5]]
    
    if (input$search_fill == 'On' && nrow(fullmap_dt)!=0){
      
      s2 = fill_route(fullmap_dt, total_trip, uncollected, react_list$gjson, time=start_time)
      
      total_trip <- s2[[1]]
      total_trip$color <- factor(total_trip$color, levels = total_trip$color)
      fullmap_dt <- s2[[2]]
      react_list$gjson <- s2[[3]]
      
    }
    
    if (nrow(fullmap_dt)==0){
      output$no_routes_cvrp <- renderText({reason})
      
      output$total_vehicles_kpi <- renderText({''})
      output$total_distance_kpi_cvrp <- renderText({''})
      output$total_load_kpi <- renderText({''})
      output$total_fuel_kpi <- renderText({''})
      
      output$distance_bar <- renderText({''})
      output$load_bar <- renderText({''})
      
      output$mymap_cvrp <- renderLeaflet({
        leaflet() %>%
          addProviderTiles(provider = providers$CartoDB.Voyager)%>%
          setView(lng=23.717613, lat=37.967271, zoom = 15)
      })
      
      output$selectv_render <- renderUI({})
      
    }
    
    else{
      
      output$no_routes_cvrp <- renderText({''})
      
      nofv <-  nrow(total_trip)
      if (nofv == react_list$previous){
        react_list$flag = NULL
        react_list$flag = TRUE
      }
      react_list$previous <- nofv
      
      available <- input$nofvehicles
      
      output$total_vehicles_kpi <- renderText({paste(nofv, " of ", available, " available")})
      total_distance <- round(sum(total_trip['total_distance'])/1000, 2)
      output$total_distance_kpi_cvrp <- renderText({paste(total_distance, " km")})
      total_load <- sum(total_trip['total_load'])
      output$total_load_kpi <- renderText({paste(formatC(total_load, big.mark=','), " units")})
      total_fuel <- round(sum(total_trip['total_distance'])/100000 * 78.4, 2)
      total_cost <- round(total_fuel*2.145, 2)
      output$total_fuel_kpi <- renderText({paste(total_fuel, " litres (", total_cost, " eur )")})
      
      xidx <- as.numeric(row.names(total_trip))
      output$distance_bar <- renderPlot({
        ggplot(total_trip)+
          xlab("Vehicle ID") + ylab("Total distance (km)")+
          geom_bar(stat="identity", position="dodge",
                   show.legend = FALSE, aes(x=xidx, y=round(total_distance/1000, 2), fill=color))+
          geom_label(aes(x=xidx, y=round(total_distance/1000, 2), label=round(total_distance/1000, 2)), size=6)+ # vjust=+0.30,
          scale_fill_manual(values=hex_colours[xidx])+
          theme(
            panel.background = element_rect(fill='white'), #transparent panel bg
            # plot.background = element_rect(fill='#E9E9E9'), #transparent plot bg
            panel.grid.major = element_line(colour='#E9E9E9'),
            panel.grid.minor = element_line(colour='#E9E9E9'),
            axis.text.x=element_blank(),
            axis.ticks.x=element_blank(),
            axis.title.x = element_blank(),
            axis.title.y = element_text(size = 18),
            axis.text.y = element_text(size = 14)
          )

      })
      
      output$load_bar <- renderPlot({ggplot(total_trip)+
          xlab("Vehicle ID") + ylab("Total load")+
          geom_bar(stat="identity", position="dodge",
                   show.legend = FALSE, aes(x=xidx, y=total_load, fill=color))+
          geom_label(aes(x=xidx, y=total_load, label=total_load), size=6)+
          scale_fill_manual(values=hex_colours[xidx])+
          theme(
            panel.background = element_rect(fill='white'), #transparent panel bg
            # plot.background = element_rect(fill='#E9E9E9'), #transparent plot bg
            panel.grid.major = element_line(colour='#E9E9E9'),
            panel.grid.minor = element_line(colour='#E9E9E9'),
            axis.title.y = element_text(size = 18),
            axis.title.x = element_text(size = 18),
            axis.text.y = element_text(size = 14),
            axis.text.x = element_text(size = 14)
          )
      })
      
      
      veh_sel <- list()
      for (i in 1:nofv){veh_sel <- append(veh_sel, paste('Vehicle ', as.character(i)))}
      
      react_list$veh_used <- veh_sel
      
      output$selectv_render <- renderUI({
        awesomeCheckboxGroup(
          inputId = "chosen_vehicle",
          label = "Vehicles shown",
          choices = veh_sel,
          selected = veh_sel,
          inline=TRUE,
          status='success'
        )
      })
      
      output$mymap_cvrp <- renderLeaflet({
        leaflet() %>%
          addProviderTiles(provider = providers$CartoDB.Voyager)
      })
      
      for (i in 1:nofv) {

        map_dt <- fullmap_dt%>%
          dplyr::filter(vehicle_id==i)

        leafletProxy(mapId = "mymap_cvrp", session = session)%>%
          addCircleMarkers(
            data=map_dt,

            group = veh_sel[i],

            lng = ~cords_lng,
            lat = ~cords_lat,

            # label = ~paste(stop_count, ': ', title),
            popup = ~paste("Load: ", "<b>", node_demand, "</b>"),

            color = ~marker_col,

            fillOpacity = 1,

            labelOptions = labelOptions(noHide = T, direction = 'top', textOnly = F,
                                        style = list(
                                          "font-family" = "serif",
                                          "font-weight" = "bold",
                                          "box-shadow" = "3px 3px rgba(0,0,0,0.25)",
                                          "font-size" = "15px",
                                          "border-color" = "rgba(0,0,0,0.5)"
                                        )),

          )%>%
          fitBounds(lng1 = max(fullmap_dt$cords_lng),lat1 = max(fullmap_dt$cords_lat),
                    lng2 = min(fullmap_dt$cords_lng),lat2 = min(fullmap_dt$cords_lat))

      }
      
    }
    
    shinyjs::delay(2, {shinyjs::runjs("swal.close();")})
    
  })
  
  
  observeEvent(c(input$chosen_vehicle, react_list$flag), {
    # for (i in 1:length(react_list$veh_used)){
    # # hideGroup(group=react_list$veh_used[i])%>%
    # }
    # browser()
    leafletProxy(mapId = "mymap_cvrp", session = session) %>% 
      clearGeoJSON()
    
    
    for (i in input$chosen_vehicle){

      gjson_idx <- as.integer(str_sub(i, -1))

      leafletProxy(mapId = "mymap_cvrp", session = session) %>% 
        addGeoJSON(react_list$gjson[[gjson_idx]],
                   # group = veh_sel[i],
                   color = hex_colours[[gjson_idx]],
                   fill=FALSE,
                   opacity = '80%')
      # showGroup(group=input$chosen_vehicle)
    }
    
  })

  
})

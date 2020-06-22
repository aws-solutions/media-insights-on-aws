export default {
  updateAssetId (state, value) {
    state.display_asset_id = value
  },
  updatePlayer (state, player) {
    state.player = player
  },
  updateTimeseries (state, value){
    state.chart_tuples = value
  },
  updateCurrentTime (state, value) {
    state.current_time = value
  },
  updateSelectedLabel (state, value){
    state.selected_label = value
  },
  updateExecutedAssets (state, value){
    state.execution_history = value
  },
}

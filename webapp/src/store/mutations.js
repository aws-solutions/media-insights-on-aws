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
  updateSelectedLabel (state, value){
    state.selected_label = value
  },
}

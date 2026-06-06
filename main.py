import auth
from mcp.server.fastmcp import FastMCP
from tools import history, playlist, playback, search, library, lastfm, discovery

auth.check_env()

mcp = FastMCP("spotify-lastfm")

# Playback
mcp.tool()(playback.play)
mcp.tool()(playback.pause)
mcp.tool()(playback.next_track)
mcp.tool()(playback.previous_track)
mcp.tool()(playback.play_track)
mcp.tool()(playback.play_context)
mcp.tool()(playback.set_volume)
mcp.tool()(playback.set_shuffle)
mcp.tool()(playback.set_repeat)
mcp.tool()(playback.get_current_track)
mcp.tool()(playback.get_devices)
mcp.tool()(playback.transfer_playback)
mcp.tool()(playback.add_to_queue)

# History
mcp.tool()(history.get_recently_played)
mcp.tool()(history.get_top_tracks)
mcp.tool()(history.get_top_artists)
mcp.tool()(history.get_genre_profile)

# Search
mcp.tool()(search.search_tracks)
mcp.tool()(search.search_artists)
mcp.tool()(search.search_albums)
mcp.tool()(search.search_playlists)
mcp.tool()(search.get_this_is_playlist)

# Playlist
mcp.tool()(playlist.get_playlists)
mcp.tool()(playlist.get_playlist_tracks)
mcp.tool()(playlist.create_playlist)
mcp.tool()(playlist.add_tracks_to_playlist)
mcp.tool()(playlist.remove_tracks_from_playlist)

# Library
mcp.tool()(library.save_track)
mcp.tool()(library.unsave_track)
mcp.tool()(library.get_saved_tracks)
mcp.tool()(library.save_album)
mcp.tool()(library.get_saved_albums)
mcp.tool()(library.get_artist_albums)

# Last.fm
mcp.tool()(lastfm.get_similar_artists)
mcp.tool()(lastfm.get_artist_top_tags)
mcp.tool()(lastfm.get_artist_info)
mcp.tool()(lastfm.get_album_info)
mcp.tool()(lastfm.get_similar_tracks)
mcp.tool()(lastfm.get_tag_top_artists)

# Discovery
mcp.tool()(discovery.build_taste_profile)
mcp.tool()(discovery.find_hidden_gems)
mcp.tool()(discovery.traverse_artist_graph)
mcp.tool()(discovery.genre_bridge)
mcp.tool()(discovery.find_similar_tracks_fresh)
mcp.tool()(discovery.build_track_taste_profile)
mcp.tool()(discovery.traverse_track_graph)
mcp.tool()(discovery.analyze_listening_evolution)
mcp.tool()(discovery.analyze_discovery_rate)
mcp.tool()(discovery.analyze_mood_by_time)

if __name__ == "__main__":
    mcp.run()

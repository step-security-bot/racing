import logging
import numpy as np
import pandas as pd
from scipy.signal import savgol_filter
from sklearn.cluster import KMeans
from scipy.signal import argrelextrema


class Analyzer:
    def __init__(self):
        pass

    def resample(self, df, columns=["Brake", "SpeedMs"], freq=1):
        # https://stackoverflow.com/questions/30560198/resampling-non-time-series-data/57110084
        columns = ["DistanceRoundTrack"] + columns
        id = df["id"].iloc[0]
        df = df[columns]

        max = df["DistanceRoundTrack"].max()
        min = df["DistanceRoundTrack"].min()
        count = max
        count = int(count / freq)
        df.set_index("DistanceRoundTrack", inplace=True)
        # remove duplicates
        df = df[~df.index.duplicated(keep="first")]
        # display(df)

        resampled = np.linspace(min, max, count)
        # print(Xresampled)

        # Resampling
        # df = df.reindex(df.index.union(resampling))

        # Interpolation technique to use. One of:

        #'linear': Ignore the index and treat the values as equally spaced.
        #   This is the only method supported on MultiIndexes.
        #'time': Works on daily and higher resolution data to interpolate given length of interval.
        #'index', 'values': use the actual numerical values of the index.
        #'pad': Fill in NaNs using existing values.
        #'nearest', 'zero', 'slinear', 'quadratic', 'cubic', 'spline', 'barycentric', 'polynomial':
        #   Passed to scipy.interpolate.interp1d. These methods use the numerical values of the index.
        #   Both 'polynomial' and 'spline' require that you also specify an order (int),
        #   e.g. df.interpolate(method='polynomial', order=5).
        #'krogh', 'piecewise_polynomial', 'spline', 'pchip', 'akima':
        #   Wrappers around the SciPy interpolation methods of similar names. See Notes.
        #'from_derivatives': Refers to scipy.interpolate.BPoly.from_derivatives
        #   which replaces 'piecewise_polynomial' interpolation method in scipy 0.18.

        # df = df.reindex(df.index.union(Xresampled)).interpolate(method='polynomial',order=2).loc[Xresampled]
        df = (
            df.reindex(df.index.union(resampled))
            .interpolate(method="values")
            .loc[resampled]
        )
        df = df.reset_index()
        df["id"] = id
        return df

    def local_maxima(self, df, column="Gear", points=50):
        return self.local_extrema(df, column, mode="max", points=points)

    def local_minima(self, df, column="Gear", points=50):
        return self.local_extrema(df, column, mode="min", points=points)

    def local_extrema(self, df, column="Gear", mode="min", points=50):
        # https://stackoverflow.com/questions/48023982/pandas-finding-local-max-and-min
        # Find local peaks
        n = points  # number of points to be checked before and after
        # Find local peaks

        if column == "Gear":
            min = df.iloc[argrelextrema(df[column].values, np.less_equal, order=n)[0]][
                column
            ]
            max = df.iloc[
                argrelextrema(df[column].values, np.greater_equal, order=n)[0]
            ][column]
        else:
            min = df.iloc[argrelextrema(df[column].values, np.less, order=n)[0]][column]
            max = df.iloc[argrelextrema(df[column].values, np.greater, order=n)[0]][
                column
            ]

        # select only the indexes of minima and maximma in the original dataframe
        min_max = df.loc[min.index.union(max.index)]
        # # also add the first and last row
        min_max = pd.concat([min_max, df.iloc[[0, -1]]])

        if mode == "min":
            # now find the local minima again
            real = min_max[column][
                (min_max[column].shift(1) >= min_max[column])
                & (min_max[column].shift(-1) > min_max[column])
            ]
        else:
            # now find the local maxima again
            real = min_max[column][
                (min_max[column].shift(1) <= min_max[column])
                & (min_max[column].shift(-1) < min_max[column])
            ]

        return df.loc[real.index]

    def local_minima_off(self, df, column="Gear"):
        # https://stackoverflow.com/questions/48023982/pandas-finding-local-max-and-min
        # Find local peaks
        # df['max'] = df.Gear[(df.Gear.shift(1) <= df.Gear) & (df.Gear.shift(-1) < df.Gear)]
        # df = in_df.copy()

        min = df[column][
            (df[column].shift(1) >= df[column]) & (df[column].shift(-1) > df[column])
        ]
        max = df[column][
            (df[column].shift(1) <= df[column]) & (df[column].shift(-1) < df[column])
        ]

        # select only the indexes of minima in the original dataframe
        min_max = df.loc[min.index.union(max.index)]
        # also add the first and last row
        min_max = pd.concat([min_max, df.iloc[[0, -1]]])

        # now find the local minima again
        real_min = min_max[column][
            (min_max[column].shift(1) >= min_max[column])
            & (min_max[column].shift(-1) > min_max[column])
        ]
        return df.loc[real_min.index]

    def extend_lap(self, df, count=2):
        max_distance = df["DistanceRoundTrack"].max()
        df_copy = df.copy()
        for i in range(1, count + 1):
            df2 = df_copy.copy()
            df2["DistanceRoundTrack"] = df2["DistanceRoundTrack"].add(max_distance * i)
            df = pd.concat([df, df2], ignore_index=True)
        return df

    def cluster(self, minima_dfs, n_clusters=None, field="Gear"):
        df = pd.concat(minima_dfs)

        if n_clusters is None:
            # calculate the median of all lengths of all_minima array
            n_clusters = int(np.median([len(m) for m in minima_dfs]))

        # Extract the x and y coordinates of the track
        x = df[[field, "DistanceRoundTrack"]]

        # Fit a k-means model to the data
        kmeans = KMeans(n_clusters=n_clusters, n_init="auto")
        kmeans.fit(x)

        # Predict the cluster labels for each data point
        labels = kmeans.predict(x)
        # Get the centroids of all clusters
        centroids = kmeans.cluster_centers_
        # Convert the centroids to a pandas DataFrame
        centroids_df = pd.DataFrame(centroids, columns=[field, "DistanceRoundTrack"])

        return centroids_df, labels

    def remove_uncorrelated_laps(self, laps, column="SpeedMs", threshold=0.6):
        # remove laps that are too different from the others
        scores = []
        no_laps = len(laps)
        for i in range(len(laps)):
            for j in range(i + 1, len(laps)):
                correlation = laps[i][column].corr(laps[j][column])
                # print(f"{i} {j} {correlation}")
                if correlation < threshold:
                    scores.append(i)
                    scores.append(j)

        # get the most common number
        scores.sort()
        if len(scores) > 0:
            scores = np.array(scores)
            scores = np.bincount(scores)
            # display(scores)
            # max = np.argmax(scores)
            # print(max)
            # get all bins larger than 2
            scores = np.where(scores > no_laps * 0.8)[0]
            # display(scores)
            ignore_laps = scores

            for idx in ignore_laps:
                logging.debug("remove lap: " + laps[idx]["id"].iloc[0])
                # print("remove lap: " + laps[idx]["id"].iloc[0])
        else:
            ignore_laps = []

        # remove all indices from laps where the index is in ignore_laps
        return [laps[i] for i in range(len(laps)) if i not in ignore_laps]

    def drop_decreasing(self, df, column="DistanceRoundTrack"):
        # drop all rows where the distance is decreasing
        # df = df[df[column].diff() > 0]
        cols = [column]
        mon_inc = (df[cols].cummax().diff().fillna(0.1) > 0).all(axis=1)
        return df[mon_inc]

    def make_monotonic(self, distances, points):
        # Iterate over the tracks
        max_distance = distances[0]
        selected_idx = []
        for idx in range(distances.shape[0]):
            # If distance is higher than previous distance, select the point
            if distances[idx] > max_distance:
                selected_idx.append(idx)
                max_distance = distances[idx]

        return distances[selected_idx], points[selected_idx]

    def track_length(self, distances):
        length = 0
        for lap in distances:
            max_distance = lap.max()
            if max_distance > length:
                length = max_distance
        return length

    def resample_(self, distances, points, length):
        delta_distance = 2  # [meter]
        distances = distances.copy()
        points = points.copy()
        resampled_distances = np.arange(0, length, delta_distance)
        x = points[:, 0]
        y = points[:, 1]
        x_n = np.interp(resampled_distances, distances, x, left=np.nan, right=np.nan)
        y_n = np.interp(resampled_distances, distances, y, left=np.nan, right=np.nan)

        return resampled_distances, np.column_stack((x_n, y_n))

    def remove_outliers(self, points):
        # Laps have some extream telemetry message.
        # These outliers need to be filled with nan values.
        #  If yaw angle changes more than a threshold, this point is accepted as extreme
        delta_distance = 2  # [radian]
        threshold = 0.4  # [radian]
        filter_window = 60  # [meter]

        filter_window_index = filter_window / delta_distance
        points = points.copy()

        # If yaw angle is higher than a threshold
        # Fill filter window with nan values
        differences = np.diff(points, axis=0)
        yaw_angles = np.arctan2(differences[:, 0], differences[:, 1])
        mask = ~np.isnan(yaw_angles)
        yaw_angles[mask] = np.unwrap(yaw_angles[mask])
        yaw_changes = np.diff(yaw_angles)
        for point_idx in range(points.shape[0] - 2):
            if abs(yaw_changes[point_idx]) > threshold:
                start = int(max(0, point_idx - filter_window_index))
                end = int(min(points.shape[0] - 1, point_idx + filter_window_index))
                points[start:end, :] = np.nan

        return points

    def merge_track_points(self, distances_a, points_a, length):
        delta_distance = 2  # [meter]
        filter_window = 60
        # filter_order = 2
        filter_window_index = filter_window / delta_distance

        track_distances = []
        track_points = []
        num_samples = int(length / delta_distance)

        # Iterate over sample points
        for point_idx in range(num_samples):
            window_distances = []
            window_x = []
            window_y = []
            # Iterate over the laps
            for lap_idx in range(len(distances_a)):
                distances = distances_a[lap_idx].copy()
                points = points_a[lap_idx].copy()
                # Calculate start and end index of filter window
                start = int(max(0, point_idx - filter_window_index))
                end = int(min(num_samples - 1, point_idx + filter_window_index))
                # Get points in filter window
                window_distances.extend(distances[start:end])
                window_x.extend(points[start:end, 0])
                window_y.extend(points[start:end, 1])

            window_distances = np.array(window_distances)
            window_x = np.array(window_x)
            window_y = np.array(window_y)
            window_distances = window_distances[~np.isnan(window_x)]
            window_y = window_y[~np.isnan(window_x)]
            window_x = window_x[~np.isnan(window_x)]
            # Fit a polynom to points in filter windows
            px = np.polyfit(window_distances, window_x, 2)
            py = np.polyfit(window_distances, window_y, 2)
            fx = np.poly1d(px)
            fy = np.poly1d(py)
            # Calculate the point by using polynomial
            p = np.array([fx(distances[point_idx]), fy(distances[point_idx])])
            track_distances.append(distances[point_idx])
            track_points.append(p)

        return np.array(track_distances), np.array(track_points)

    def yaw_changes(self, points):
        # distances = distances.copy()
        # points = points.copy()
        # Yaw changes can be calculated by track points
        differences = np.diff(points, axis=0)
        yaw_angles = np.arctan2(differences[:, 0], differences[:, 1])
        yaw_angles = np.unwrap(yaw_angles)
        yaw_changes = np.diff(yaw_angles)
        yaw_changes = np.pad(yaw_changes, (0, 2), "constant", constant_values=(0, 0))
        # Yawy changes are filtered with savgol filter.
        yaw_changes = savgol_filter(yaw_changes, 20, 1)
        return yaw_changes

    def track_sections(self, distances, yaw_changes, threshold=0.0051):
        min_threshold = threshold
        threshold = min_threshold

        cw_max = 0
        cw_start_idx = 0
        cw_started = False
        ccw_max = 0
        ccw_started = False
        ccw_start_idx = 0
        str_started = False
        str_max = 0
        str_start_idx = 0
        sections = []

        # Iterate over sample points
        for point_idx in range(20, distances.shape[0]):
            # Check last index
            last_index = point_idx == distances.shape[0] - 1
            # Reset threshold
            if abs(yaw_changes[point_idx]) < min_threshold:
                threshold = min_threshold
            # Check clock wise corner started and ended
            if not cw_started:
                if yaw_changes[point_idx] > threshold:
                    cw_max = 0
                    cw_started = True
                    cw_start_idx = point_idx
            else:
                cw_max = max(cw_max, abs(yaw_changes[point_idx]))
                threshold = max(min_threshold, abs(cw_max / 2))
                if last_index or (yaw_changes[point_idx] <= threshold):
                    cw_started = False
                    sec = {
                        "type": "clock_wise",
                        "start": distances[cw_start_idx],
                        "end": distances[point_idx],
                        "max_yaw_change": cw_max,
                    }
                    sections.append(sec)
            # Check counter clock wise corner started and ended
            if not ccw_started:
                if yaw_changes[point_idx] < -threshold:
                    ccw_max = 0
                    ccw_started = True
                    ccw_start_idx = point_idx
            else:
                ccw_max = max(ccw_max, abs(yaw_changes[point_idx]))
                threshold = max(min_threshold, abs(ccw_max / 2))
                if last_index or (yaw_changes[point_idx] >= -threshold):
                    ccw_started = False
                    sec = {
                        "type": "counter_clock_wise",
                        "start": distances[ccw_start_idx],
                        "end": distances[point_idx],
                        "max_yaw_change": ccw_max,
                    }
                    sections.append(sec)
            # Check straigh section started and ended
            if not str_started:
                if abs(yaw_changes[point_idx]) < threshold:
                    str_max = 0
                    str_started = True
                    str_start_idx = point_idx
            else:
                str_max = max(str_max, yaw_changes[point_idx])
                if last_index or (abs(yaw_changes[point_idx]) >= threshold):
                    str_started = False
                    sec = {
                        "type": "straight",
                        "start": distances[str_start_idx],
                        "end": distances[point_idx],
                        "max_yaw_change": str_max,
                    }
                    sections.append(sec)

        return sections

    # # This function split data for multiple laps
    # def split_laps(self, distances, points, threshold=100):
    #     laps = []
    #     prev_idx = 0
    #     for idx in range(1, distances.shape[0]):
    #         # If DistanceRoundTrack dropped significantly, this is a new lap
    #         passed_start = distances[idx] - distances[idx-1] < -threshold
    #         last_point = (idx == distances.shape[0]-1)
    #         if passed_start or last_point:
    #             lap_distances = distances[prev_idx:idx]
    #             lap_points = points[prev_idx:idx]
    #             lap = {'distances': lap_distances,
    #                 'points': lap_points}
    #             laps.append(lap)
    #             prev_idx = idx
    #     return laps['distances'], laps['points']
